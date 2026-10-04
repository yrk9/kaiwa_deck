from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import limits
from app.core.security import get_current_user_id
from app.crud import card as crud
from app.db.session import get_db
from app.models import Card
from app.schemas.card import CardIn, CardOut

# 全部のAPIをログイン必須にして、つけ忘れを防ぐ
router = APIRouter(
    prefix="/card",
    tags=["cards"],
    dependencies=[Depends(get_current_user_id)],
)


def _get_card_or_404(db: Session, card_id: UUID) -> Card:
    card = crud.get_card(db, card_id)
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Card not found")
    return card


def _get_own_card(db: Session, card_id: UUID, user_id: UUID) -> Card:
    card = _get_card_or_404(db, card_id)
    # 公式のお題(create_user_idがNULL)は誰とも一致しないので、ここで弾かれる
    if card.create_user_id != user_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Not the owner of this card"
        )
    return card


@router.get("/", response_model=list[CardOut])
def list_cards(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return crud.list_cards(db, user_id)


@router.post("/", response_model=CardOut, status_code=status.HTTP_201_CREATED)
def create_card(
    body: CardIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if crud.count_cards_by_user(db, user_id) >= limits.MAX_CARDS_PER_USER:
        raise HTTPException(status.HTTP_409_CONFLICT, "Card limit reached")
    return crud.create_card(db, user_id, body)


@router.get("/{card_id}/", response_model=CardOut)
def read_card(card_id: UUID, db: Session = Depends(get_db)):
    return _get_card_or_404(db, card_id)


@router.put("/{card_id}/", response_model=CardOut)
def update_card(
    card_id: UUID,
    body: CardIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    card = _get_own_card(db, card_id, user_id)
    return crud.update_card(db, card, body)


@router.delete("/{card_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    card = _get_own_card(db, card_id, user_id)
    crud.delete_card(db, card)
