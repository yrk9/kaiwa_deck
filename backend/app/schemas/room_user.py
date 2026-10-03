from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RoomUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    room_id: UUID
    user_id: UUID
    joined_at: datetime
    last_seen_at: datetime


class RoomMemberOut(RoomUserOut):
    """参加者一覧用。表示のためにuser_nameも持つ。"""

    user_name: str
