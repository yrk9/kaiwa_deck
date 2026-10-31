from uuid import UUID

from sqlalchemy.orm import Session

from app.models import CardNote


def get_note(db: Session, user_id: UUID, card_id: UUID) -> CardNote | None:
    return db.get(CardNote, {"user_id": user_id, "card_id": card_id})


def save_note(
    db: Session, user_id: UUID, card_id: UUID, note: str
) -> CardNote:
    # 1つのお題にメモは1つなので、すでにあれば上書きする
    card_note = get_note(db, user_id, card_id)
    if card_note is None:
        card_note = CardNote(user_id=user_id, card_id=card_id, note=note)
        db.add(card_note)
    else:
        card_note.note = note
    db.commit()
    db.refresh(card_note)
    return card_note


def delete_note(db: Session, card_note: CardNote) -> None:
    db.delete(card_note)
    db.commit()
