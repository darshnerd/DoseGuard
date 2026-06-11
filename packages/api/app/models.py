from datetime import UTC, date, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class DrugConcept(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    canonical_name: str
    normalized_name: str = Field(index=True, unique=True)
    rxcui: str | None = None

class DrugInfo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    concept_normalized: str = Field(index=True, unique=True)
    cid: int | None = None
    atc_code: str | None = None
    drug_class: str | None = None
    indication: str | None = None
    mechanism: str | None = None
    food_interactions: str | None = None
    warnings: str | None = None
    black_box: bool = False

class DrugAlias(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    alias_normalized: str = Field(index=True)
    concept_normalized: str = Field(index=True)
    country: str | None = None
    source: str = "unknown"


class MedicineProduct(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    name_normalized: str = Field(index=True)
    manufacturer: str | None = None
    country: str = "IN"
    source: str = "unknown"


class ProductIngredient(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(index=True, foreign_key="medicineproduct.id")
    ingredient_normalized: str = Field(index=True)
    strength: str | None = None

class Interaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    a_norm: str = Field(index=True)
    b_norm: str = Field(index=True)
    severity: str = "moderate"
    description: str | None = None
    mechanism: str | None = None
    management: str | None = None
    references_json: str | None = None
    sources: str = ""

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    token_version: int = Field(default=0)
    full_name: str | None = None
    age: int | None = None
    sex: str | None = None
    timezone: str = Field(default="Asia/Kolkata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Medication(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    name: str
    start_date: date = Field(default_factory=lambda: datetime.now(UTC).date())
    duration_days: int | None = None

class MedicationIngredient(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    medication_id: int = Field(index=True, foreign_key="medication.id")
    ingredient: str = Field(index=True)
    rxcui: str | None = None

class ScanHistory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    drugs: list[str] = Field(default_factory=list, sa_column = Column(JSON))
    conflict_found: bool = False
    interaction_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class DoseSchedule(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    medication_id: int = Field(index=True, foreign_key="medication.id")
    slot: str


class DoseLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    medication_id: int = Field(index=True, foreign_key="medication.id")
    slot: str
    status: str
    taken_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
