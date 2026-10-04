"""ルームAPI(/room)のテスト。

確認していること:
- 作成(201)・参照・更新・削除(204)が、API設計どおりの形で動く
- 作成すると、作成者が最初の参加者として登録される
- 参照は、ログインしていれば誰でもできる(ルームの作成者でなくてもOK)
- 更新・削除は作成者本人だけ(他人は403、存在しないidは404)
- 使えるデッキは「ルームの参加者のデッキ」だけ。作成時は自分のデッキのみ、
  更新時は参加者が持つデッキならOK、参加者以外のデッキは403
- デッキを別のものに変更すると、引いた記録はリセットされる。
  ルーム名だけの変更では、リセットされない
- 存在しないデッキは404、入力が不正なら422
- ログイン(トークン)が無いと、どのルートも401

確認していないこと:
- 本物のDB(Postgres)での動作。ここではメモリ上のSQLiteを使うため、
  ルーム削除時のroom_usersの連鎖削除(ON DELETE CASCADE)は確認できない
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import get_current_user_id
from app.db.base import Base
from app.db.session import get_db
from app.main import app as api
from app.models import Deck, RoomDrawnCard, RoomUser

USER_A = uuid.uuid4()
USER_B = uuid.uuid4()


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
    login_as(USER_A)
    yield TestClient(api)
    api.dependency_overrides.clear()


@pytest.fixture
def make_deck(session_factory):
    def _make(owner_id, name="デッキ"):
        with session_factory() as db:
            deck = Deck(create_user_id=owner_id, deck_name=name)
            db.add(deck)
            db.commit()
            return deck.id

    return _make


def body_for(deck_id, name="懇親会ルーム"):
    return {"deck_id": str(deck_id), "room_name": name}


def create(client, deck_id, name="懇親会ルーム"):
    return client.post("/room/", json=body_for(deck_id, name))


def add_drawn(session_factory, room_id):
    with session_factory() as db:
        db.add(RoomDrawnCard(room_id=uuid.UUID(room_id), card_id=uuid.uuid4()))
        db.commit()


def drawn_count(session_factory, room_id):
    with session_factory() as db:
        query = db.query(RoomDrawnCard).filter_by(room_id=uuid.UUID(room_id))
        return query.count()


def test_create_room(client, make_deck):
    deck_id = make_deck(USER_A)
    r = create(client, deck_id)
    assert r.status_code == 201
    room = r.json()
    assert room["room_create_user"] == str(USER_A)
    assert room["deck_id"] == str(deck_id)
    assert room["room_name"] == "懇親会ルーム"
    uuid.UUID(room["id"])


def test_creator_becomes_first_member(client, make_deck, session_factory):
    room = create(client, make_deck(USER_A)).json()
    with session_factory() as db:
        member = db.get(
            RoomUser,
            {"room_id": uuid.UUID(room["id"]), "user_id": USER_A},
        )
    assert member is not None


def test_create_with_unknown_deck_is_404(client):
    assert create(client, uuid.uuid4()).status_code == 404


def test_create_with_other_users_deck_is_403(client, make_deck):
    deck_id = make_deck(USER_B)
    assert create(client, deck_id).status_code == 403


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"room_name": "名前だけ"}, id="no-deck"),
        pytest.param({"deck_id": "not-a-uuid", "room_name": "x"}, id="bad-id"),
        pytest.param({"deck_id": str(uuid.uuid4())}, id="no-name"),
        pytest.param(
            {"deck_id": str(uuid.uuid4()), "room_name": ""}, id="empty-name"
        ),
        pytest.param(
            {"deck_id": str(uuid.uuid4()), "room_name": "あ" * 101},
            id="name-too-long",
        ),
    ],
)
def test_create_rejects_invalid_input(client, body):
    assert client.post("/room/", json=body).status_code == 422


def test_read_room(client, make_deck):
    room = create(client, make_deck(USER_A)).json()
    r = client.get(f"/room/{room['id']}/")
    assert r.status_code == 200
    assert r.json() == room


def test_any_logged_in_user_can_read_room(client, make_deck):
    room = create(client, make_deck(USER_A)).json()
    login_as(USER_B)
    assert client.get(f"/room/{room['id']}/").status_code == 200


def test_read_unknown_room_is_404(client):
    assert client.get(f"/room/{uuid.uuid4()}/").status_code == 404


def test_creator_can_update_name_and_deck(client, make_deck):
    room = create(client, make_deck(USER_A)).json()
    new_deck_id = make_deck(USER_A, "別のデッキ")
    r = client.put(
        f"/room/{room['id']}/", json=body_for(new_deck_id, "新しい名前")
    )
    assert r.status_code == 200
    assert r.json()["room_name"] == "新しい名前"
    assert r.json()["deck_id"] == str(new_deck_id)
    assert client.get(f"/room/{room['id']}/").json() == r.json()


def test_changing_deck_resets_drawn(client, make_deck, session_factory):
    room = create(client, make_deck(USER_A)).json()
    add_drawn(session_factory, room["id"])

    new_deck_id = make_deck(USER_A, "別のデッキ")
    r = client.put(f"/room/{room['id']}/", json=body_for(new_deck_id))
    assert r.status_code == 200
    assert drawn_count(session_factory, room["id"]) == 0


def test_renaming_room_keeps_drawn(client, make_deck, session_factory):
    deck_id = make_deck(USER_A)
    room = create(client, deck_id).json()
    add_drawn(session_factory, room["id"])

    r = client.put(f"/room/{room['id']}/", json=body_for(deck_id, "改名"))
    assert r.status_code == 200
    assert drawn_count(session_factory, room["id"]) == 1


def test_update_with_deck_of_another_member(
    client, make_deck, session_factory
):
    room = create(client, make_deck(USER_A)).json()
    with session_factory() as db:
        db.add(RoomUser(room_id=uuid.UUID(room["id"]), user_id=USER_B))
        db.commit()
    deck_of_b = make_deck(USER_B)
    r = client.put(f"/room/{room['id']}/", json=body_for(deck_of_b))
    assert r.status_code == 200
    assert r.json()["deck_id"] == str(deck_of_b)


def test_update_with_deck_of_non_member_is_403(client, make_deck):
    room = create(client, make_deck(USER_A)).json()
    deck_of_b = make_deck(USER_B)  # BはまだルームにいないのでNG
    r = client.put(f"/room/{room['id']}/", json=body_for(deck_of_b))
    assert r.status_code == 403


def test_update_with_unknown_deck_is_404(client, make_deck):
    room = create(client, make_deck(USER_A)).json()
    r = client.put(f"/room/{room['id']}/", json=body_for(uuid.uuid4()))
    assert r.status_code == 404


def test_other_user_cannot_update(client, make_deck):
    deck_id = make_deck(USER_A)
    room = create(client, deck_id).json()
    login_as(USER_B)
    r = client.put(f"/room/{room['id']}/", json=body_for(deck_id, "乗っ取り"))
    assert r.status_code == 403
    login_as(USER_A)
    assert client.get(f"/room/{room['id']}/").json() == room


def test_update_unknown_room_is_404(client, make_deck):
    r = client.put(
        f"/room/{uuid.uuid4()}/", json=body_for(make_deck(USER_A))
    )
    assert r.status_code == 404


def test_creator_can_delete(client, make_deck):
    room = create(client, make_deck(USER_A)).json()
    assert client.delete(f"/room/{room['id']}/").status_code == 204
    assert client.get(f"/room/{room['id']}/").status_code == 404


def test_other_user_cannot_delete(client, make_deck):
    room = create(client, make_deck(USER_A)).json()
    login_as(USER_B)
    assert client.delete(f"/room/{room['id']}/").status_code == 403
    login_as(USER_A)
    assert client.get(f"/room/{room['id']}/").status_code == 200


def test_delete_unknown_room_is_404(client):
    assert client.delete(f"/room/{uuid.uuid4()}/").status_code == 404


@pytest.mark.parametrize(
    "method, path",
    [
        ("post", "/room/"),
        ("get", f"/room/{uuid.uuid4()}/"),
        ("put", f"/room/{uuid.uuid4()}/"),
        ("delete", f"/room/{uuid.uuid4()}/"),
    ],
)
def test_all_routes_require_login(client, method, path):
    del api.dependency_overrides[get_current_user_id]
    r = client.request(method, path, json=body_for(uuid.uuid4()))
    assert r.status_code == 401
