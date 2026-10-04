from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import Room, RoomDrawnCard, RoomUser
from app.schemas.room import RoomIn


def create_room(db: Session, user_id: UUID, data: RoomIn) -> Room:
    room = Room(
        room_create_user=user_id,
        deck_id=data.deck_id,
        room_name=data.room_name,
    )
    db.add(room)
    db.flush()  # room.idを使うため、先にDBへ送る
    # 作成者は最初の参加者として登録する
    db.add(RoomUser(room_id=room.id, user_id=user_id))
    db.commit()
    db.refresh(room)
    return room


def count_rooms_created_by(db: Session, user_id: UUID) -> int:
    stmt = select(func.count()).where(Room.room_create_user == user_id)
    return db.execute(stmt).scalar_one()


def get_room(db: Session, room_id: UUID) -> Room | None:
    return db.get(Room, room_id)


def is_room_member(db: Session, room_id: UUID, user_id: UUID) -> bool:
    key = {"room_id": room_id, "user_id": user_id}
    return db.get(RoomUser, key) is not None


def update_room(db: Session, room: Room, data: RoomIn) -> Room:
    # デッキを変えたら、前のデッキで引いた記録は消す(同じ保存の中で行う)
    if room.deck_id != data.deck_id:
        db.execute(
            delete(RoomDrawnCard).where(RoomDrawnCard.room_id == room.id)
        )
    room.deck_id = data.deck_id
    room.room_name = data.room_name
    db.commit()
    db.refresh(room)
    return room


def delete_room(db: Session, room: Room) -> None:
    db.delete(room)
    db.commit()
