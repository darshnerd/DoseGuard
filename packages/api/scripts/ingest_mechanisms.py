import csv

from _common import SOURCES


def read():
    with open(SOURCES / "ddi_mechanisms.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            action = (r.get("action") or "").strip()
            mech = (r.get("mechanism") or "").strip()
            text = " ".join(p for p in (action, mech) if p) or None
            yield r["drugA"], r["drugB"], {
                "mechanism": text,
                "source": "DrugBank",
            }
