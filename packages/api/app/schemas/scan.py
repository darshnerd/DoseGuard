from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.drug import ResolvedDrug
from app.schemas.interaction import InteractionResult


class ScanResponse(BaseModel):
    detected: list[ResolvedDrug]
    ingredients: list[str]
    conflict_found: bool
    interactions: list[InteractionResult]


class ScanRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    drugs: list[str]
    conflict_found: bool
    interaction_count: int
    created_at: datetime

class ScanUpdate(BaseModel):
    drugs: list[str]