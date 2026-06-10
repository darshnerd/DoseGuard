import json

from _common import SEV_NAME, SOURCES


def read():
    data = json.load(open(SOURCES / "curated.json", encoding="utf-8"))
    for bucket in data.get("drug_interactions", {}).values():
        for r in bucket:
            yield r["drug_a"], r["drug_b"], {
                "severity": SEV_NAME.get((r.get("severity") or "").lower(), "moderate"),
                "mechanism": r.get("mechanism"),
                "description": r.get("effect"),
                "management": r.get("Safer_alternative"),
                "source": "Curated",
            }
