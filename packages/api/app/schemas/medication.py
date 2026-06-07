from pydantic import BaseModel, ConfigDict


class MedicationCreate(BaseModel):
    name: str


class MedicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    ingredient: str | None
    rxcui: str | None