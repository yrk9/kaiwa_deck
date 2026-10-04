from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import RoomUser, User


def join_room(
    db: Session, room_id: UUID, user_id: UUID
) -> tuple[RoomUser, bool]:
    # 戻り値は(参加情報, 初めての参加かどうか)
    member = db.get(RoomUser, {"room_id": room_id, "user_id": user_id})
    is_new = member is None
    if is_new:
        member = RoomUser(room_id=room_id, user_id=user_id)
        db.add(member)
    else:
        # 再入室は新しい行を作らず、最終アクセスだけ更新する
        member.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(member)
    return member, is_new


def count_members(db: Session, room_id: UUID) -> int:
    stmt = select(func.count()).where(RoomUser.room_id == room_id)
    return db.execute(stmt).scalar_one()


def get_member(db: Session, room_id: UUID, user_id: UUID) -> RoomUser | None:
    return db.get(RoomUser, {"room_id": room_id, "user_id": user_id})


def leave_room(db: Session, member: RoomUser) -> None:
    db.delete(member)
    db.commit()


def list_members(db: Session, room_id: UUID) -> list[tuple[RoomUser, str]]:
    stmt = (
        select(RoomUser, User.user_name)
        .join(User, User.id == RoomUser.user_id)
        .where(RoomUser.room_id == room_id)
        .order_by(RoomUser.joined_at)
    )
    return list(db.execute(stmt).all())
