from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CardNoteIn(BaseModel):
    """想定回答のメモの保存で受け取る内容。"""

    model_config = ConfigDict(str_strip_whitespace=True)

    # 空のメモは保存せず、消すときはDELETEを使う
    note: str = Field(min_length=1, max_length=2000)


class CardNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    card_id: UUID
    note: str
    updated_at: datetime
