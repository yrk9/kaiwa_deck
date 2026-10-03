from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Card, DeckCard, Room, RoomDrawnCard


def _pick_undrawn_card(db: Session, room: Room) -> Card | None:
    drawn_ids = select(RoomDrawnCard.card_id).where(
        RoomDrawnCard.room_id == room.id
    )
    stmt = (
        select(Card)
        .join(DeckCard, DeckCard.card_id == Card.id)
        .where(DeckCard.deck_id == room.deck_id, Card.id.not_in(drawn_ids))
        .order_by(func.random())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def draw_card(db: Session, room: Room) -> tuple[RoomDrawnCard, Card] | None:
    # 引けるお題が残っていなければNoneを返す
    while True:
        card = _pick_undrawn_card(db, room)
        if card is None:
            return None
        drawn = RoomDrawnCard(room_id=room.id, card_id=card.id)
        db.add(drawn)
        try:
            db.commit()
        except IntegrityError:
            # 同時に同じお題を引かれたので選び直す(残りは必ず減るので終わる)
            db.rollback()
            continue
        db.refresh(drawn)
        return drawn, card


def list_drawn(db: Session, room_id: UUID) -> list[tuple[RoomDrawnCard, Card]]:
    stmt = (
        select(RoomDrawnCard, Card)
        .join(Card, Card.id == RoomDrawnCard.card_id)
        .where(RoomDrawnCard.room_id == room_id)
        .order_by(RoomDrawnCard.drawn_at)
    )
    return list(db.execute(stmt).all())


def reset_drawn(db: Session, room_id: UUID) -> None:
    db.execute(delete(RoomDrawnCard).where(RoomDrawnCard.room_id == room_id))
    db.commit()
