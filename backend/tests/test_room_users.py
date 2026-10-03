"""ルームの参加・一覧・退出(/room/{room_id}/user)のテスト。

確認していること:
- 参加すると201で、参加情報(room_id, user_id, joined_at, last_seen_at)を返す
- 再入室は新しい行を作らず200を返し、last_seenだけ更新してjoined_atは変えない
- 参加者一覧は、user_nameつきで、参加が早い順に返る
- 参加・一覧とも、ログインしていれば誰でもできる(参加者でなくても見られる)
- 退出(204)は本人だけ。他の人を外すのは、作成者でも403
- 作成者が退出すると、ルームは解散(削除)される
- 作成者以外が退出しても、ルームは残り、再入室もできる
- ルームのデッキの持ち主が退出しても、デッキはそのまま
- 参加していない人の退出や、存在しないルームは404
- ログイン(トークン)が無いと401

確認していないこと:
- 本物のDB(Postgres)での動作。ここではメモリ上のSQLiteを使うため、
  ルーム解散時のroom_usersの連鎖削除は確認できない
"""
import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import get_current_user_id
from app.db.base import Base
from app.db.session import get_db
from app.main import app as api
from app.models import Deck, Room, RoomUser, User

USER_A = uuid.uuid4()
USER_B = uuid.uuid4()
OLD_TIME = datetime(2000, 1, 1, 12, 0, 0)


def login_as(user_id):
    api.dependency_overrides[get_current_user_id] = lambda: user_id


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False)


@pytest.fixture
def client(session_factory):
    def override_get_db():
        with session_factory() as db:
            yield db

    api.dependency_overrides[get_db] = override_get_db
    login_as(USER_B)
    yield TestClient(api)
    api.dependency_overrides.clear()


@pytest.fixture
def room_id(session_factory):
    with session_factory() as db:
        room = Room(
            room_create_user=USER_A, deck_id=uuid.uuid4(), room_name="部屋"
        )
        db.add_all(
            [
                User(id=USER_A, user_name="Aさん"),
                User(id=USER_B, user_name="Bさん"),
                room,
            ]
        )
        db.commit()
        return room.id


def add_member(session_factory, room_id, user_id):
    with session_factory() as db:
        db.add(RoomUser(room_id=room_id, user_id=user_id))
        db.commit()


def test_join_room(client, room_id):
    r = client.post(f"/room/{room_id}/user/")
    assert r.status_code == 201
    member = r.json()
    assert member["room_id"] == str(room_id)
    assert member["user_id"] == str(USER_B)
    assert member["joined_at"]
    assert member["last_seen_at"]


def test_rejoin_updates_last_seen_only(client, room_id, session_factory):
    # 前に入った記録を、わざと昔の時刻にしておく
    with session_factory() as db:
        db.add(
            RoomUser(
                room_id=room_id,
                user_id=USER_B,
                joined_at=OLD_TIME,
                last_seen_at=OLD_TIME,
            )
        )
        db.commit()

    r = client.post(f"/room/{room_id}/user/")
    assert r.status_code == 200
    member = r.json()
    assert datetime.fromisoformat(member["joined_at"]) == OLD_TIME
    assert datetime.fromisoformat(member["last_seen_at"]) > OLD_TIME


def test_rejoin_does_not_add_a_row(client, room_id, session_factory):
    client.post(f"/room/{room_id}/user/")
    client.post(f"/room/{room_id}/user/")
    with session_factory() as db:
        count = db.query(RoomUser).filter_by(room_id=room_id).count()
    assert count == 1


def test_join_unknown_room_is_404(client):
    assert client.post(f"/room/{uuid.uuid4()}/user/").status_code == 404


def test_list_members_with_user_name_in_join_order(
    client, room_id, session_factory
):
    # 登録の順番とは逆の時刻にして、参加が早い順になるか確かめる
    with session_factory() as db:
        db.add_all(
            [
                RoomUser(
                    room_id=room_id,
                    user_id=USER_B,
                    joined_at=OLD_TIME + timedelta(hours=1),
                    last_seen_at=OLD_TIME,
                ),
                RoomUser(
                    room_id=room_id,
                    user_id=USER_A,
                    joined_at=OLD_TIME,
                    last_seen_at=OLD_TIME,
                ),
            ]
        )
        db.commit()

    r = client.get(f"/room/{room_id}/user/")
    assert r.status_code == 200
    members = r.json()
    assert [m["user_name"] for m in members] == ["Aさん", "Bさん"]
    assert members[0]["user_id"] == str(USER_A)
    assert set(members[0]) == {
        "room_id",
        "user_id",
        "user_name",
        "joined_at",
        "last_seen_at",
    }


def test_non_member_can_list_members(client, room_id):
    # Bはまだ参加していないが、一覧は見られる
    assert client.get(f"/room/{room_id}/user/").status_code == 200


def test_list_members_of_unknown_room_is_404(client):
    assert client.get(f"/room/{uuid.uuid4()}/user/").status_code == 404


def test_member_can_leave_and_rejoin(client, room_id, session_factory):
    add_member(session_factory, room_id, USER_A)
    add_member(session_factory, room_id, USER_B)

    assert client.delete(f"/room/{room_id}/user/{USER_B}/").status_code == 204
    members = client.get(f"/room/{room_id}/user/").json()
    assert [m["user_id"] for m in members] == [str(USER_A)]
    assert client.get(f"/room/{room_id}/").status_code == 200
    assert client.post(f"/room/{room_id}/user/").status_code == 201


def test_cannot_remove_another_member(client, room_id, session_factory):
    add_member(session_factory, room_id, USER_A)
    add_member(session_factory, room_id, USER_B)

    # BがAを外そうとする
    assert client.delete(f"/room/{room_id}/user/{USER_A}/").status_code == 403
    # 作成者のAでも、Bを外すことはできない
    login_as(USER_A)
    assert client.delete(f"/room/{room_id}/user/{USER_B}/").status_code == 403

    members = client.get(f"/room/{room_id}/user/").json()
    assert {m["user_id"] for m in members} == {str(USER_A), str(USER_B)}


def test_creator_leaving_disbands_room(client, room_id, session_factory):
    add_member(session_factory, room_id, USER_A)
    add_member(session_factory, room_id, USER_B)
    login_as(USER_A)

    assert client.delete(f"/room/{room_id}/user/{USER_A}/").status_code == 204
    assert client.get(f"/room/{room_id}/").status_code == 404


def test_deck_stays_when_its_owner_leaves(client, room_id, session_factory):
    with session_factory() as db:
        deck = Deck(create_user_id=USER_B, deck_name="Bのデッキ")
        db.add(deck)
        db.flush()
        deck_id = deck.id
        db.get(Room, room_id).deck_id = deck_id
        db.commit()
    add_member(session_factory, room_id, USER_B)

    assert client.delete(f"/room/{room_id}/user/{USER_B}/").status_code == 204
    with session_factory() as db:
        assert db.get(Room, room_id).deck_id == deck_id
        assert db.get(Deck, deck_id) is not None


def test_leave_when_not_a_member_is_404(client, room_id):
    assert client.delete(f"/room/{room_id}/user/{USER_B}/").status_code == 404


def test_leave_unknown_room_is_404(client):
    path = f"/room/{uuid.uuid4()}/user/{USER_B}/"
    assert client.delete(path).status_code == 404


def test_leave_requires_login(client, room_id):
    del api.dependency_overrides[get_current_user_id]
    r = client.delete(f"/room/{room_id}/user/{USER_B}/")
    assert r.status_code == 401


@pytest.mark.parametrize("method", ["post", "get"])
def test_requires_login(client, room_id, method):
    del api.dependency_overrides[get_current_user_id]
    r = client.request(method, f"/room/{room_id}/user/")
    assert r.status_code == 401
