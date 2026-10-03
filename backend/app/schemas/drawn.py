from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DrawnOut(BaseModel):
    room_id: UUID
    card_id: UUID
    drawn_at: datetime
    content: str
    description: str | None
