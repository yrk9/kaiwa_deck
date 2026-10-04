from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core import limits
from app.core.security import get_current_user_id
from app.crud import room as room_crud
from app.crud import room_user as crud
from app.db.session import get_db
from app.models import Room
from app.schemas.room_user import RoomMemberOut, RoomUserOut

# 全部のAPIをログイン必須にして、つけ忘れを防ぐ
router = APIRouter(
    prefix="/room",
    tags=["room_users"],
    dependencies=[Depends(get_current_user_id)],
)


def _get_room_or_404(db: Session, room_id: UUID) -> Room:
    room = room_crud.get_room(db, room_id)
    if room is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Room not found")
    return room


@router.post(
    "/{room_id}/user/",
    response_model=RoomUserOut,
    status_code=status.HTTP_201_CREATED,
)
def join_room(
    room_id: UUID,
    response: Response,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _get_room_or_404(db, room_id)
    # 満員でも、参加済みの人の再入室は通す
    is_member = crud.get_member(db, room_id, user_id) is not None
    full = crud.count_members(db, room_id) >= limits.MAX_USERS_PER_ROOM
    if full and not is_member:
        raise HTTPException(status.HTTP_409_CONFLICT, "Room is full")
    member, is_new = crud.join_room(db, room_id, user_id)
    if not is_new:
        # 再入室は何も作っていないので、201ではなく200にする
        response.status_code = status.HTTP_200_OK
    return member


@router.get("/{room_id}/user/", response_model=list[RoomMemberOut])
def list_members(room_id: UUID, db: Session = Depends(get_db)):
    _get_room_or_404(db, room_id)
    # 参加者一覧は、ルーム参照と同じく、ログインしていれば誰でも見られる
    return [
        RoomMemberOut(
            room_id=member.room_id,
            user_id=member.user_id,
            joined_at=member.joined_at,
            last_seen_at=member.last_seen_at,
            user_name=user_name,
        )
        for member, user_name in crud.list_members(db, room_id)
    ]


@router.delete(
    "/{room_id}/user/{user_id}/", status_code=status.HTTP_204_NO_CONTENT
)
def leave_room(
    room_id: UUID,
    user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    room = _get_room_or_404(db, room_id)
    # 他の参加者を退出させることはできない(作成者でも本人だけ)
    if user_id != current_user_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "You can only remove yourself"
        )
    member = crud.get_member(db, room_id, user_id)
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not a member")
    # 作成者が抜けたら、ルームを解散する(ルームごと削除)
    if room.room_create_user == user_id:
        room_crud.delete_room(db, room)
    else:
        crud.leave_room(db, member)
