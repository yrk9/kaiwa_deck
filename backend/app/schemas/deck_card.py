from uuid import UUID

from pydantic import BaseModel


class DeckCardIn(BaseModel):
    card_id: UUID


class DeckCardOut(BaseModel):
    deck_id: UUID
    card_id: UUID
