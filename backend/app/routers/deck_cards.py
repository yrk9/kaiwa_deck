from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import limits
from app.core.security import get_current_user_id
from app.crud import card as card_crud
from app.crud import deck as deck_crud
from app.crud import deck_card as crud
from app.db.session import get_db
from app.models import Deck
from app.schemas.card import CardOut
from app.schemas.deck_card import DeckCardIn, DeckCardOut

# デッキに紐づく中間テーブルの操作なので、decks.pyとは別ファイルに分けている
router = APIRouter(
    prefix="/deck",
    tags=["deck_cards"],
    dependencies=[Depends(get_current_user_id)],
)


# decks.pyと同じ内容。_付きは内部用なので、共有せずこちらにも置く
def _get_own_deck(db: Session, deck_id: UUID, user_id: UUID) -> Deck:
    deck = deck_crud.get_deck(db, deck_id)
    if deck is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deck not found")
    if deck.create_user_id != user_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Not the owner of this deck"
        )
    return deck


@router.get("/{deck_id}/cards/", response_model=list[CardOut])
def list_cards(
    deck_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _get_own_deck(db, deck_id, user_id)
    return crud.list_cards_in_deck(db, deck_id)


@router.post(
    "/{deck_id}/cards/",
    response_model=DeckCardOut,
    status_code=status.HTTP_201_CREATED,
)
def add_card(
    deck_id: UUID,
    body: DeckCardIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _get_own_deck(db, deck_id, user_id)
    card = card_crud.get_card(db, body.card_id)
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Card not found")
    # 公式(作成者なし)か自分のお題だけ入れられる。他人のお題は、あとから変わりうるため
    if card.create_user_id not in (None, user_id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Only official cards or your own cards can be added",
        )
    # 同じお題の二重登録は断る
    if crud.get_deck_card(db, deck_id, body.card_id) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Card is already in this deck"
        )
    if crud.count_cards_in_deck(db, deck_id) >= limits.MAX_CARDS_PER_DECK:
        raise HTTPException(status.HTTP_409_CONFLICT, "Deck is full")
    return crud.add_card_to_deck(db, deck_id, body.card_id)


@router.delete(
    "/{deck_id}/cards/{card_id}/", status_code=status.HTTP_204_NO_CONTENT
)
def remove_card(
    deck_id: UUID,
    card_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _get_own_deck(db, deck_id, user_id)
    deck_card = crud.get_deck_card(db, deck_id, card_id)
    if deck_card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Card not in this deck")
    crud.remove_card_from_deck(db, deck_card)
