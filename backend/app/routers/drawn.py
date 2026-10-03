from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.crud import drawn as crud
from app.db.session import get_db
from app.models import Card, RoomDrawnCard
from app.routers.room_access import get_room_as_member
from app.schemas.drawn import DrawnOut

# 全部のAPIをログイン必須にして、つけ忘れを防ぐ
router = APIRouter(
    prefix="/room",
    tags=["drawn"],
    dependencies=[Depends(get_current_user_id)],
)


def _to_out(drawn: RoomDrawnCard, card: Card) -> DrawnOut:
    return DrawnOut(
        room_id=drawn.room_id,
        card_id=drawn.card_id,
        drawn_at=drawn.drawn_at,
        content=card.content,
        description=card.description,
    )


@router.post(
    "/{room_id}/drawn/",
    response_model=DrawnOut,
    status_code=status.HTTP_201_CREATED,
)
def draw_card(
    room_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    room = get_room_as_member(db, room_id, user_id)
    result = crud.draw_card(db, room)
    if result is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "No cards left to draw"
        )
    drawn, card = result
    return _to_out(drawn, card)


@router.get("/{room_id}/drawn/", response_model=list[DrawnOut])
def list_drawn(
    room_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    get_room_as_member(db, room_id, user_id)
    # 引いた順に並べる
    return [_to_out(d, c) for d, c in crud.list_drawn(db, room_id)]


@router.delete("/{room_id}/drawn/", status_code=status.HTTP_204_NO_CONTENT)
def reset_drawn(
    room_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    get_room_as_member(db, room_id, user_id)
    crud.reset_drawn(db, room_id)
