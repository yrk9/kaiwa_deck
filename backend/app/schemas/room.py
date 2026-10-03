from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoomIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    deck_id: UUID
    room_name: str = Field(min_length=1, max_length=100)


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_create_user: UUID
    deck_id: UUID
    room_name: str
    created_at: datetime
