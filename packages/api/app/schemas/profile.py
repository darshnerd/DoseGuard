from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None
    age: int | None
    sex: str | None
    created_at: datetime


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    age: int | None = None
    sex: str | None = None
    