import csv

from _common import SEV_NAME, SOURCES


def read():
    with open(SOURCES / "ddinter.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            yield r["Drug_A"], r["Drug_B"], {
                "severity": SEV_NAME.get((r["Level"] or "").lower(), "moderate"),
                "source": "DDInter",
            }
