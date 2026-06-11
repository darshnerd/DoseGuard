from pydantic import BaseModel


class ResolvedDrug(BaseModel):
    query: str
    matched: bool = False
    rxcui: str | None = None
    name: str | None = None
    ingredient_rxcui: str | None = None
    ingredient_name: str | None = None
    ingredient_names: list[str] = []