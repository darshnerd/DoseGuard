from pydantic import BaseModel

from app.schemas.drug import ResolvedDrug
from app.schemas.interaction import InteractionResult


class ScanResponse(BaseModel):
    detected: list[ResolvedDrug]
    ingredients: list[str]
    conflict_found: bool
    interactions: list[InteractionResult]