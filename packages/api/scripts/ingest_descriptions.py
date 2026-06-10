import csv

from _common import SOURCES


def read():
    with open(SOURCES / "ddi_descriptions.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            yield r["Drug 1"], r["Drug 2"], {
                "description": r["Interaction Description"], "source": "DrugBank",
            }
