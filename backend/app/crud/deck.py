from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Card, Deck, DeckCard, Room
from app.schemas.deck import DeckIn


def create_deck(db: Session, user_id: UUID, data: DeckIn) -> Deck:
    deck = Deck(create_user_id=user_id, deck_name=data.deck_name)
    db.add(deck)
    db.flush()  # deck.idを使うため、先にDBへ送る
    if data.include_official_cards:
        official_ids = list(
            db.scalars(select(Card.id).where(Card.create_user_id.is_(None)))
        )
        db.add_all(
            DeckCard(deck_id=deck.id, card_id=card_id)
            for card_id in official_ids
        )
    db.commit()
    db.refresh(deck)
    return deck


def count_decks(db: Session, user_id: UUID) -> int:
    stmt = select(func.count()).where(Deck.create_user_id == user_id)
    return db.execute(stmt).scalar_one()


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


def is_deck_in_use(db: Session, deck_id: UUID) -> bool:
    stmt = select(Room.id).where(Room.deck_id == deck_id).limit(1)
    return db.execute(stmt).first() is not None


def delete_deck(db: Session, deck: Deck) -> None:
    db.delete(deck)
    db.commit()
