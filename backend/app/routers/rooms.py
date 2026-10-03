from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.crud import deck as deck_crud
from app.crud import room as crud
from app.db.session import get_db
from app.models import Deck, Room
from app.schemas.room import RoomIn, RoomOut

# ルーター全体にログイン必須をかけ、認証のつけ忘れを防ぐ
router = APIRouter(
    prefix="/room",
    tags=["rooms"],
    dependencies=[Depends(get_current_user_id)],
)


def _get_room_or_404(db: Session, room_id: UUID) -> Room:
    room = crud.get_room(db, room_id)
    if room is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Room not found")
    return room


def _get_own_room(db: Session, room_id: UUID, user_id: UUID) -> Room:
    room = _get_room_or_404(db, room_id)
    if room.room_create_user != user_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Not the owner of this room"
        )
    return room


def _get_deck_or_404(db: Session, deck_id: UUID) -> Deck:
    deck = deck_crud.get_deck(db, deck_id)
    if deck is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deck not found")
    return deck


@router.post("/", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(
    body: RoomIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    deck = _get_deck_or_404(db, body.deck_id)
    # 作成時点の参加者は作成者だけなので、使えるのは自分のデッキのみ
    if deck.create_user_id != user_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Deck is not owned by a room member"
        )
    return crud.create_room(db, user_id, body)


@router.get("/{room_id}/", response_model=RoomOut)
def read_room(room_id: UUID, db: Session = Depends(get_db)):
    # 作成者でなくても見られる(リンクで人を誘うため)
    return _get_room_or_404(db, room_id)


@router.put("/{room_id}/", response_model=RoomOut)
def update_room(
    room_id: UUID,
    body: RoomIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    room = _get_own_room(db, room_id, user_id)
    deck = _get_deck_or_404(db, body.deck_id)
    # 使えるのは、ルームの参加者が持つデッキだけ
    if not crud.is_room_member(db, room.id, deck.create_user_id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Deck is not owned by a room member"
        )
    return crud.update_room(db, room, body)


@router.delete("/{room_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(
    room_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    room = _get_own_room(db, room_id, user_id)
    crud.delete_room(db, room)
