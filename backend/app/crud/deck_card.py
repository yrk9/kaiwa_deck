from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Card, DeckCard


def card_exists(db: Session, card_id: UUID) -> bool:
    return db.get(Card, card_id) is not None


def get_deck_card(
    db: Session, deck_id: UUID, card_id: UUID
) -> DeckCard | None:
    # 主キーが2つ(deck_idとcard_id)なので、辞書で指定する
    return db.get(DeckCard, {"deck_id": deck_id, "card_id": card_id})


def add_card_to_deck(db: Session, deck_id: UUID, card_id: UUID) -> DeckCard:
    deck_card = DeckCard(deck_id=deck_id, card_id=card_id)
    db.add(deck_card)
    db.commit()
    return deck_card


def remove_card_from_deck(db: Session, deck_card: DeckCard) -> None:
    db.delete(deck_card)
    db.commit()
