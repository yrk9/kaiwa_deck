from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeckIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    deck_name: str = Field(min_length=1, max_length=100)
    # trueなら、公式のお題を全部入れた状態でデッキを作る
    include_official_cards: bool = False


class DeckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    create_user_id: UUID
    deck_name: str
    created_at: datetime
    updated_at: datetime


class DeckListOut(DeckOut):
    card_count: int
