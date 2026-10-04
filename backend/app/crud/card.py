from uuid import UUID

from sqlalchemy import or_, select
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


def list_cards(db: Session, user_id: UUID) -> list[Card]:
    # 公式(作成者なし)と自分のお題だけ。公式が先で、その中は内容の順
    stmt = (
        select(Card)
        .where(
            or_(Card.create_user_id.is_(None), Card.create_user_id == user_id)
        )
        .order_by(Card.create_user_id.is_not(None), Card.content, Card.id)
    )
    return list(db.scalars(stmt))


def update_card(db: Session, card: Card, data: CardIn) -> Card:
    card.content = data.content
    card.description = data.description
    db.commit()
    db.refresh(card)
    return card


def delete_card(db: Session, card: Card) -> None:
    db.delete(card)
    db.commit()
