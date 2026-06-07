from pydantic import BaseModel


class InteractionCheckRequest(BaseModel):
    drugs: list[str]


class InteractionResult(BaseModel):
    ingredient_a: str
    ingredient_b: str
    severity: str
    description: str


class InteractionCheckResponse(BaseModel):
    drugs: list[str]
    ingredients: list[str]
    conflict_found: bool
    interactions: list[InteractionResult]