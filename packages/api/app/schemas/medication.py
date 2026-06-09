from pydantic import BaseModel, ConfigDict


class IngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient: str
    rxcui: str | None


class MedicationCreate(BaseModel):
    name: str
    drugs: list[str] | None = None


class MedicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    ingredients: list[IngredientOut] = []
