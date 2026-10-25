from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.card import CardCategory


class DeckIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    deck_name: str = Field(min_length=1, max_length=100)
    # trueなら、公式のお題を全部入れて作る(公開中の古いフロントのために残している)
    include_official_cards: bool = False
    # 指定すると、その種類の公式のお題だけを入れて作る
    official_category: CardCategory | None = None

    @model_validator(mode="after")
    def check_one_official_option(self) -> "DeckIn":
        # どちらが優先か迷わないよう、同時の指定は誤り(422)にする
        if self.include_official_cards and self.official_category:
            raise ValueError(
                "include_official_cards and official_category "
                "cannot be used together"
            )
        return self


class DeckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    create_user_id: UUID
    deck_name: str
    created_at: datetime
    updated_at: datetime


class DeckListOut(DeckOut):
    card_count: int
