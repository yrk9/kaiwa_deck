from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Card
from app.schemas.card import CardIn


def create_card(db: Session, user_id: UUID, data: CardIn) -> Card:
    card = Card(
        create_user_id=user_id,
        content=data.content,
        description=data.description,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def get_card(db: Session, card_id: UUID) -> Card | None:
    return db.get(Card, card_id)


def update_card(db: Session, card: Card, data: CardIn) -> Card:
    card.content = data.content
    card.description = data.description
    db.commit()
    db.refresh(card)
    return card


def delete_card(db: Session, card: Card) -> None:
    db.delete(card)
    db.commit()
