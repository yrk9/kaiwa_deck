from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.crud import drawn as drawn_crud
from app.crud import room_user as member_crud
from app.db.session import get_db
from app.routers.room_access import get_room_as_member
from app.schemas.room import RoomOut
from app.schemas.state import RoomStateOut, StateDrawn, StateParticipant

# 全部のAPIをログイン必須にして、つけ忘れを防ぐ
router = APIRouter(
    prefix="/room",
    tags=["room_state"],
    dependencies=[Depends(get_current_user_id)],
)


@router.get("/{room_id}/state/", response_model=RoomStateOut)
def read_state(
    room_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # ルーム画面の最初の表示に必要な情報を、1回でまとめて返す
    room = get_room_as_member(db, room_id, user_id)
    return RoomStateOut(
        room=RoomOut.model_validate(room),
        participants=[
            StateParticipant(
                user_id=m.user_id,
                user_name=user_name,
                joined_at=m.joined_at,
                last_seen_at=m.last_seen_at,
            )
            for m, user_name in member_crud.list_members(db, room_id)
        ],
        remaining_card_count=drawn_crud.count_remaining(db, room),
        drawn=[
            StateDrawn(
                card_id=d.card_id,
                content=c.content,
                description=c.description,
                drawn_at=d.drawn_at,
            )
            for d, c in drawn_crud.list_drawn(db, room_id)
        ],
    )
