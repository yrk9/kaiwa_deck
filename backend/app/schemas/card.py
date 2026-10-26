from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# 公式デッキの種類。DBのcheck制約(0002_card_category.sql)と同じ値にする
CardCategory = Literal["interview", "reverse_question", "small_talk"]


class CardIn(BaseModel):
    """お題の作成・更新で受け取る内容。"""

    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=500)


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    create_user_id: UUID | None
    content: str
    description: str | None
    category: CardCategory | None
