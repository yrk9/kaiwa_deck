from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.crud import room as room_crud
from app.models import Room


def get_room_as_member(db: Session, room_id: UUID, user_id: UUID) -> Room:
    """ルームを返す。参加者でなければ403、ルームが無ければ404。"""
    room = room_crud.get_room(db, room_id)
    if room is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Room not found")
    if not room_crud.is_room_member(db, room_id, user_id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Not a member of this room"
        )
    return room
