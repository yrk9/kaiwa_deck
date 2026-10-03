from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Room, RoomUser
from app.schemas.room import RoomIn


def create_room(db: Session, user_id: UUID, data: RoomIn) -> Room:
    room = Room(
        room_create_user=user_id,
        deck_id=data.deck_id,
        room_name=data.room_name,
    )
    db.add(room)
    db.flush()  # room.idを確定させる
    # 作成者は最初の参加者として登録する
    db.add(RoomUser(room_id=room.id, user_id=user_id))
    db.commit()
    db.refresh(room)
    return room


def get_room(db: Session, room_id: UUID) -> Room | None:
    return db.get(Room, room_id)


def is_room_member(db: Session, room_id: UUID, user_id: UUID) -> bool:
    key = {"room_id": room_id, "user_id": user_id}
    return db.get(RoomUser, key) is not None


def update_room(db: Session, room: Room, data: RoomIn) -> Room:
    room.deck_id = data.deck_id
    room.room_name = data.room_name
    db.commit()
    db.refresh(room)
    return room


def delete_room(db: Session, room: Room) -> None:
    db.delete(room)
    db.commit()
