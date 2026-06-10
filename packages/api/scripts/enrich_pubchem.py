import asyncio

from _common import DB, worse

from sqlmodel import Session, create_engine, select

from app.models import DrugConcept, Interaction
from app.services.pubchem import live_pairs

BATCH = 80


async def _run():
    engine = create_engine(f"sqlite:///{DB}")
    with Session(engine) as session:
        names = session.exec(select(DrugConcept.normalized_name)).all()
        existing = {
            (i.a_norm, i.b_norm): i for i in session.exec(select(Interaction)).all()
        }
        added = 0
        for start in range(0, len(names), BATCH):
            chunk = names[start:start + BATCH]
            for pair in await live_pairs(chunk):
                key = (pair["ingredient_a"], pair["ingredient_b"])
                row = existing.get(key)
                if row:
                    row.severity = worse(row.severity, pair["severity"])
                    if "PubChem" not in row.sources:
                        row.sources = ",".join(filter(None, [row.sources, "PubChem"]))
                    if not row.description and pair.get("description"):
                        row.description = pair["description"]
                    session.add(row)
                else:
                    row = Interaction(
                        a_norm=key[0], b_norm=key[1],
                        severity=pair["severity"],
                        description=pair.get("description"),
                        sources="PubChem",
                    )
                    session.add(row)
                    existing[key] = row
                    added += 1
            session.commit()
        print(f"pubchem_added={added}")


def main():
    asyncio.run(_run())


if __name__ == "__main__":
    main()
    