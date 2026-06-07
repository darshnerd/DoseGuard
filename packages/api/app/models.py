from sqlmodel import Field, SQLModel


class Interaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ingredient_a: str = Field(index=True)
    ingredient_b: str = Field(index=True)
    severity: str
    description: str
    