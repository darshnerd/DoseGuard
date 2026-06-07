from sqlmodel import Session, select

from app.db import engine, init_db
from app.models import Interaction

CURATED = [
    ("warfarin", "aspirin", "severe", "Significantly increased bleeding risk."),
    ("warfarin", "ibuprofen", "severe", "Increased GI bleeding risk."),
    ("ibuprofen", "lisinopril", "moderate", "Reduced blood-pressure control; kidney injury risk."),
    ("lisinopril", "spironolactone", "severe", "Hyperkalemia risk (dangerous potassium levels)."),
    ("simvastatin", "clarithromycin", "contraindicated", "Severe muscle damage; do not combine."),
    ("methotrexate", "ibuprofen", "severe", "Increased methotrexate toxicity."),
    ("lithium", "ibuprofen", "severe", "Raises lithium to toxic levels."),
    ("digoxin", "clarithromycin", "severe", "Raises digoxin to toxic levels."),
]


def seed():
    init_db()
    with Session(engine) as session:
        for a, b, severity, description in CURATED:
            a, b = sorted([a.lower(), b.lower()])
            exists = session.exec(
                select(Interaction).where(
                    (Interaction.ingredient_a == a) & (Interaction.ingredient_b == b)
                )
            ).first()
            if not exists:
                session.add(
                    Interaction(
                        ingredient_a=a,
                        ingredient_b=b,
                        severity=severity,
                        description=description,
                    )
                )
        session.commit()


if __name__ == "__main__":
    seed()
    print(f"Seeded {len(CURATED)} interactions.")
