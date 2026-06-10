
import asyncio
import time
import urllib.parse

import httpx
from sqlmodel import Session, create_engine, select

from _common import DB, normalize

from app.models import DrugAlias, DrugConcept

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
CONCURRENCY = 4
MIN_INTERVAL = 0.22          # keep under PubChem's 5 req/sec

_lock = asyncio.Lock()
_last = 0.0


async def _throttle():
    global _last
    async with _lock:
        wait = _last + MIN_INTERVAL - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        _last = time.monotonic()


def _usable(syn):
    s = syn.strip()
    if not (3 <= len(s) <= 40):          # drop codes and IUPAC monsters
        return False
    return any(c.isalpha() for c in s)   # drop CAS / registry numbers


async def _synonyms(client, name):
    await _throttle()
    q = urllib.parse.quote(name, safe="")
    try:
        r = await client.get(f"{BASE}/compound/name/{q}/synonyms/JSON")
        if r.status_code != 200:
            return []
        return r.json()["InformationList"]["Information"][0].get("Synonym", [])
    except Exception:  # noqa: BLE001
        return []


async def _run(limit=None):
    engine = create_engine(f"sqlite:///{DB}")
    with Session(engine) as session:
        concepts = session.exec(select(DrugConcept)).all()
        existing = {
            (a.alias_normalized, a.concept_normalized)
            for a in session.exec(select(DrugAlias)).all()
        }
    if limit:
        concepts = concepts[:limit]

    sem = asyncio.Semaphore(CONCURRENCY)
    rows = []
    async with httpx.AsyncClient(timeout=20.0) as client:
        async def work(concept):
            async with sem:
                syns = await _synonyms(client, concept.canonical_name)
            for syn in syns:
                if not _usable(syn):
                    continue
                an = normalize(syn)
                if not an or an == concept.normalized_name:
                    continue
                key = (an, concept.normalized_name)
                if key in existing:
                    continue
                existing.add(key)
                rows.append(DrugAlias(
                    alias_normalized=an,
                    concept_normalized=concept.normalized_name,
                    source="PubChem",
                ))

        await asyncio.gather(*(work(c) for c in concepts))

    with Session(engine) as session:
        session.add_all(rows)
        session.commit()
    print(f"aliases_added={len(rows)}")


def main():
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(_run(limit))


if __name__ == "__main__":
    main()
    