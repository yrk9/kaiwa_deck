from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Deck, DeckCard
from app.schemas.deck import DeckIn


def create_deck(db: Session, user_id: UUID, data: DeckIn) -> Deck:
    deck = Deck(create_user_id=user_id, deck_name=data.deck_name)
    db.add(deck)
    db.commit()
    db.refresh(deck)
    return deck


def get_deck(db: Session, deck_id: UUID) -> Deck | None:
    return db.get(Deck, deck_id)


def list_decks_with_card_count(
    db: Session, user_id: UUID
) -> list[tuple[Deck, int]]:
    card_count = func.count(DeckCard.card_id)
    # お題が0枚のデッキも一覧に出すため、outerjoinを使う
    stmt = (
        select(Deck, card_count)
        .outerjoin(DeckCard, DeckCard.deck_id == Deck.id)
        .where(Deck.create_user_id == user_id)
        .group_by(Deck.id)
        .order_by(Deck.created_at.desc())
    )
    return list(db.execute(stmt).all())


def delete_deck(db: Session, deck: Deck) -> None:
    db.delete(deck)
    db.commit()
