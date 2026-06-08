from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Interaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ingredient_a: str = Field(index=True)
    ingredient_b: str = Field(index=True)
    severity: str
    description: str

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    token_version: int = Field(default=0)
    full_name: str | None = None
    age: int | None = None
    sex: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Medication(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    name: str
    ingredient: str | None = None
    rxcui: str | None = None


class ScanHistory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    drugs: list[str] = Field(default_factory=list, sa_column = Column(JSON))
    conflict_found: bool = False
    interaction_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
