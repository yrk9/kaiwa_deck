from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.room import RoomOut


class StateParticipant(BaseModel):
    user_id: UUID
    user_name: str
    joined_at: datetime
    last_seen_at: datetime


class StateDrawn(BaseModel):
    card_id: UUID
    content: str
    description: str | None
    drawn_at: datetime
    # 自分の想定回答のメモ。他の参加者のメモは返さない
    note: str | None


class RoomStateOut(BaseModel):
    room: RoomOut
    participants: list[StateParticipant]
    # 山札の中身は返さず、枚数だけ返す(ネタバレ防止)
    remaining_card_count: int
    drawn: list[StateDrawn]
