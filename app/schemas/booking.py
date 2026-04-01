from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, field_validator


class BookingCreate(BaseModel):
    room_id: int
    user_name: str
    start_time: datetime
    end_time: datetime
    timezone: str

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Проверяет что timezone — валидный IANA-идентификатор (Europe/Moscow и т.д.)."""
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, KeyError):
            raise ValueError(
                f"Unknown timezone: '{v}'. Use IANA name, e.g. 'Europe/Moscow'."
            )
        return v

    @field_validator("end_time")
    @classmethod
    def end_must_be_after_start(cls, end_time: datetime, info) -> datetime:
        start = info.data.get("start_time")
        if start is not None and end_time <= start:
            raise ValueError("end_time must be strictly after start_time")
        return end_time


class BookingResponse(BaseModel):
    id: int
    room_id: int
    user_name: str
    start_time: datetime
    end_time: datetime
    timezone: str

    model_config = {"from_attributes": True}