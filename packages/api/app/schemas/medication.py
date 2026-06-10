from datetime import date

from pydantic import BaseModel, ConfigDict


class IngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient: str
    rxcui: str | None


class MedicationCreate(BaseModel):
    name: str
    drugs: list[str] | None = None
    duration_days: int | None = None
    start_date: date | None = None


class MedicationUpdate(BaseModel):
    name: str | None = None
    duration_days: int | None = None
    start_date: date | None = None


class MedicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_date: date
    duration_days: int | None
    ingredients: list[IngredientOut] = []
