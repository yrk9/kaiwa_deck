from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.models import Card, CardNote, Deck, DeckCard


def get_deck_card(
    db: Session, deck_id: UUID, card_id: UUID
) -> DeckCard | None:
    # 主キーが2つ(deck_idとcard_id)なので、辞書で指定する
    return db.get(DeckCard, {"deck_id": deck_id, "card_id": card_id})


def count_cards_in_deck(db: Session, deck_id: UUID) -> int:
    stmt = select(func.count()).where(DeckCard.deck_id == deck_id)
    return db.execute(stmt).scalar_one()


def list_cards_in_deck(
    db: Session, deck_id: UUID, user_id: UUID
) -> list[tuple[Card, str | None, int]]:
    # 公式のお題は他人のデッキにも入るので、自分のデッキだけを数える
    other = aliased(DeckCard)
    deck_count = (
        select(func.count())
        .select_from(other)
        .join(Deck, Deck.id == other.deck_id)
        .where(other.card_id == Card.id, Deck.create_user_id == user_id)
        .scalar_subquery()
    )
    # 自分のメモだけをつなげる。メモが無いお題はNoneになる
    stmt = (
        select(Card, CardNote.note, deck_count)
        .join(DeckCard, DeckCard.card_id == Card.id)
        .outerjoin(
            CardNote,
            (CardNote.card_id == Card.id) & (CardNote.user_id == user_id),
        )
        .where(DeckCard.deck_id == deck_id)
        # デッキを作ったときに入れた公式のお題は日時が同じなので、内容の順になる
        .order_by(DeckCard.added_at, Card.content, Card.id)
    )
    return list(db.execute(stmt).all())


def add_card_to_deck(db: Session, deck_id: UUID, card_id: UUID) -> DeckCard:
    deck_card = DeckCard(deck_id=deck_id, card_id=card_id)
    db.add(deck_card)
    db.commit()
    return deck_card


def remove_card_from_deck(db: Session, deck_card: DeckCard) -> None:
    db.delete(deck_card)
    db.commit()
