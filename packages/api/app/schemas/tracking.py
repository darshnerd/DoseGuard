from pydantic import BaseModel


class ScheduleUpdate(BaseModel):
    slots: list[str]


class ScheduleOut(BaseModel):
    medication_id: int
    name: str
    slots: list[str]


class LogCreate(BaseModel):
    medication_id: int
    slot: str
    status: str


class TodayItem(BaseModel):
    medication_id: int
    name: str
    status: str


class TodaySlot(BaseModel):
    slot: str
    items: list[TodayItem]
    warnings: list[str] = []


class TodayResponse(BaseModel):
    date: str
    slots: list[TodaySlot]
    adherence: float


class AdherenceOut(BaseModel):
    percent: float
    taken: int
    expected: int

class DayStat(BaseModel):
    date: str
    expected: int
    taken: int
