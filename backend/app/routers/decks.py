from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.crud import deck as crud
from app.db.session import get_db
from app.models import Deck
from app.schemas.deck import DeckIn, DeckListOut, DeckOut

# ルーター全体にログイン必須をかけ、認証のつけ忘れを防ぐ
router = APIRouter(
    prefix="/deck",
    tags=["decks"],
    dependencies=[Depends(get_current_user_id)],
)


def _get_own_deck(db: Session, deck_id: UUID, user_id: UUID) -> Deck:
    deck = crud.get_deck(db, deck_id)
    if deck is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deck not found")
    # デッキには「公開」の仕組みが無いので、参照も含めて本人限定にしている
    if deck.create_user_id != user_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Not the owner of this deck"
        )
    return deck


@router.get("/", response_model=list[DeckListOut])
def list_decks(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    rows = crud.list_decks_with_card_count(db, user_id)
    return [
        DeckListOut(
            id=deck.id,
            create_user_id=deck.create_user_id,
            deck_name=deck.deck_name,
            created_at=deck.created_at,
            updated_at=deck.updated_at,
            card_count=count,
        )
        for deck, count in rows
    ]


@router.post("/", response_model=DeckOut, status_code=status.HTTP_201_CREATED)
def create_deck(
    body: DeckIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return crud.create_deck(db, user_id, body)


@router.get("/{deck_id}/", response_model=DeckOut)
def read_deck(
    deck_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return _get_own_deck(db, deck_id, user_id)


@router.delete("/{deck_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_deck(
    deck_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    deck = _get_own_deck(db, deck_id, user_id)
    crud.delete_deck(db, deck)
