from uuid import UUID

from pydantic import BaseModel

from app.schemas.card import CardOut


class DeckCardIn(BaseModel):
    card_id: UUID


class DeckCardOut(BaseModel):
    deck_id: UUID
    card_id: UUID


class DeckCardItem(CardOut):
    """デッキ内のお題一覧の1件。自分の想定回答のメモつき。"""

    note: str | None
    # このお題が入っている自分のデッキの数(このデッキも含む)
    deck_count: int
