from pydantic import BaseModel


class InteractionCheckRequest(BaseModel):
    drugs: list[str]


class InteractionResult(BaseModel):
    ingredient_a: str
    ingredient_b: str
    severity: str
    description: str | None = None
    mechanism: str | None = None
    source: str | None = None


class InteractionCheckResponse(BaseModel):
    drugs: list[str]
    ingredients: list[str]
    conflict_found: bool
    interactions: list[InteractionResult]