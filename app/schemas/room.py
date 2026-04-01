from pydantic import BaseModel, field_validator


class RoomCreate(BaseModel):
    name: str
    capacity: int

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty")
        return v

    @field_validator("capacity")
    @classmethod
    def capacity_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("capacity must be a positive integer")
        return v


class RoomResponse(BaseModel):
    id: int
    name: str
    capacity: int

    model_config = {"from_attributes": True}