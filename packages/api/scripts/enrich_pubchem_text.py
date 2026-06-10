import asyncio
import re
import time
import urllib.parse

import httpx
from sqlmodel import Session, SQLModel, create_engine, select

from _common import DB

from app.models import DrugConcept, DrugInfo

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
VIEW = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound"
CONCURRENCY = 4
MIN_INTERVAL = 0.25

# only trust these sources for free-text; everything else (HSDB animal studies,
# raw research abstracts) is dropped
GOOD = {"DrugBank", "FDA Label", "LiverTox", "ChEMBL", "NCI Thesaurus (NCIt)"}

ATC_SYSTEM = {
    "A": "Alimentary tract & metabolism", "B": "Blood & blood-forming organs",
    "C": "Cardiovascular system", "D": "Dermatologicals",
    "G": "Genitourinary & sex hormones", "H": "Systemic hormonal preparations",
    "J": "Anti-infectives (systemic)", "L": "Antineoplastic & immunomodulating",
    "M": "Musculoskeletal system", "N": "Nervous system",
    "P": "Antiparasitic products", "R": "Respiratory system",
    "S": "Sensory organs", "V": "Various",
}
_ATC = re.compile(r"^[A-Z]\d{2}[A-Z]{2}\d{2}$")

_lock = asyncio.Lock()
_last = 0.0


async def _throttle():
    global _last
    async with _lock:
        wait = _last + MIN_INTERVAL - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        _last = time.monotonic()


async def _get(client, url):
    await _throttle()
    try:
        r = await client.get(url)
        if r.status_code == 200:
            return r.json()
    except Exception:  # noqa: BLE001
        pass
    return None


async def _cid(client, name):
    q = urllib.parse.quote(name, safe="")
    d = await _get(client, f"{BASE}/compound/name/{q}/cids/JSON")
    cids = (d or {}).get("IdentifierList", {}).get("CID", [])
    return cids[0] if cids else None


def _index(record):
    refs = {r["ReferenceNumber"]: r.get("SourceName") for r in record.get("Reference", [])}
    out = {}

    def walk(sec):
        for s in sec.get("Section", []):
            h = s.get("TOCHeading")
            for inf in s.get("Information", []):
                src = refs.get(inf.get("ReferenceNumber"))
                for sm in inf.get("Value", {}).get("StringWithMarkup", []) or []:
                    txt = (sm.get("String") or "").strip()
                    if txt:
                        out.setdefault(h, []).append((src, txt))
            walk(s)

    walk(record)
    return out


def _pick(items, limit=600):
    if not items:
        return None
    clean = [t for src, t in items if src in GOOD] or [t for _, t in items]
    return clean[0][:limit].strip()


def _atc(items):
    for _, t in items or []:
        t = t.strip()
        if _ATC.match(t):
            return t, ATC_SYSTEM.get(t[0])
    return None, None


async def _build(client, concept):
    cid = await _cid(client, concept.canonical_name)
    if not cid:
        return None
    doc = await _get(client, f"{VIEW}/{cid}/JSON")
    if not doc or "Record" not in doc:
        return None
    idx = _index(doc["Record"])
    code, cls = _atc(idx.get("ATC Code"))
    black = any(t.strip().lower() == "yes" for _, t in idx.get("Black Box Warning", []))
    return DrugInfo(
        concept_normalized=concept.normalized_name,
        cid=cid,
        atc_code=code,
        drug_class=cls or _pick(idx.get("Drug Classes"), 120),
        indication=_pick(idx.get("Drug Indication")),
        mechanism=_pick(idx.get("Mechanism of Action")),
        food_interactions=_pick(idx.get("Drug-Food Interactions"), 400),
        warnings=_pick(idx.get("Drug Warnings"), 400),
        black_box=black,
    )


async def _run(limit=None):
    engine = create_engine(f"sqlite:///{DB}")
    import app.models  # noqa: F401  (register tables)
    SQLModel.metadata.create_all(engine)        # creates DrugInfo, leaves the rest

    with Session(engine) as session:
        concepts = session.exec(select(DrugConcept)).all()
        done = {d.concept_normalized for d in session.exec(select(DrugInfo)).all()}
    todo = [c for c in concepts if c.normalized_name not in done]
    if limit:
        todo = todo[:limit]

    sem = asyncio.Semaphore(CONCURRENCY)
    rows = []
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        async def work(c):
            async with sem:
                try:
                    info = await _build(client, c)
                except Exception:  # noqa: BLE001
                    info = None
            if info:
                rows.append(info)

        await asyncio.gather(*(work(c) for c in todo))

    with Session(engine) as session:
        session.add_all(rows)
        session.commit()
    print(f"druginfo_rows={len(rows)} of {len(todo)} attempted")


def main():
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(_run(limit))


if __name__ == "__main__":
    main()
    