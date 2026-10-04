"""デッキAPI(/deck)のテスト。

確認していること:
- 作成(201)・一覧・参照・削除(204)が、API設計どおりの形で動く
- デッキには「公開」の仕組みが無いので、参照・更新・削除は作成者本人だけ。
  他人のデッキは403、一覧にも出てこない
- 一覧のcard_countが、デッキに入っているお題の枚数と一致する
- include_official_cards=trueで作ると、公式のお題が全部入る(他人のお題は入らない)。
  省略・falseなら空のデッキ。真偽値でない値は422
- ルームが使っているデッキは削除できず409。ルームが無くなれば削除できる
- 存在しないidは404、空や長すぎる入力は422
- ログイン(トークン)が無いと、どのルートも401

確認していないこと:
- 本物のDB(Postgres)での動作。ここではメモリ上のSQLiteを使う
- デッキへのお題の追加・削除そのもの(別のテストで扱う)
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
from app.models import Card, DeckCard, Room

USER_A = uuid.uuid4()
USER_B = uuid.uuid4()
BODY = {"deck_name": "就活懇親会デッキ"}


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


def create(client, body=BODY):
    return client.post("/deck/", json=body)


def test_create_deck(client):
    r = create(client)
    assert r.status_code == 201
    deck = r.json()
    assert deck["create_user_id"] == str(USER_A)
    assert deck["deck_name"] == BODY["deck_name"]
    uuid.UUID(deck["id"])


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({}, id="no-name"),
        pytest.param({"deck_name": ""}, id="empty-name"),
        pytest.param({"deck_name": "   "}, id="blank-name"),
        pytest.param({"deck_name": "あ" * 101}, id="name-too-long"),
    ],
)
def test_create_deck_rejects_invalid_input(client, body):
    assert create(client, body).status_code == 422


def add_cards(session_factory, official_count):
    """公式のお題と、他人のお題を1件ずつ入れておく。"""
    with session_factory() as db:
        db.add_all([Card(content=f"公式{i}") for i in range(official_count)])
        db.add(Card(content="他人のお題", create_user_id=USER_B))
        db.commit()


def card_count_of(client, deck_id):
    decks = client.get("/deck/").json()
    return next(d["card_count"] for d in decks if d["id"] == deck_id)


def test_create_deck_with_official_cards(client, session_factory):
    add_cards(session_factory, official_count=3)
    r = create(
        client, {"deck_name": "公式入り", "include_official_cards": True}
    )
    assert r.status_code == 201
    assert set(r.json()) == {
        "id",
        "create_user_id",
        "deck_name",
        "created_at",
        "updated_at",
    }
    # 公式の3件だけ入り、他人のお題は入らない
    assert card_count_of(client, r.json()["id"]) == 3


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"deck_name": "x"}, id="omitted"),
        pytest.param(
            {"deck_name": "x", "include_official_cards": False}, id="false"
        ),
    ],
)
def test_create_deck_without_option_is_empty(client, session_factory, body):
    add_cards(session_factory, official_count=3)
    r = create(client, body)
    assert r.status_code == 201
    assert card_count_of(client, r.json()["id"]) == 0


def test_create_deck_with_option_but_no_official_cards(client):
    r = create(client, {"deck_name": "x", "include_official_cards": True})
    assert r.status_code == 201
    assert card_count_of(client, r.json()["id"]) == 0


def test_create_deck_rejects_non_boolean_option(client):
    body = {"deck_name": "x", "include_official_cards": "abc"}
    assert create(client, body).status_code == 422


def test_read_deck(client):
    deck = create(client).json()
    r = client.get(f"/deck/{deck['id']}/")
    assert r.status_code == 200
    assert r.json() == deck


def test_read_unknown_deck_is_404(client):
    assert client.get(f"/deck/{uuid.uuid4()}/").status_code == 404


def test_other_user_cannot_read(client):
    deck = create(client).json()
    login_as(USER_B)
    assert client.get(f"/deck/{deck['id']}/").status_code == 403


def test_other_user_cannot_delete(client):
    deck = create(client).json()
    login_as(USER_B)
    assert client.delete(f"/deck/{deck['id']}/").status_code == 403
    login_as(USER_A)
    assert client.get(f"/deck/{deck['id']}/").status_code == 200


def test_owner_can_delete(client):
    deck = create(client).json()
    assert client.delete(f"/deck/{deck['id']}/").status_code == 204
    assert client.get(f"/deck/{deck['id']}/").status_code == 404


def test_cannot_delete_deck_used_by_room(client, session_factory):
    deck = create(client).json()
    with session_factory() as db:
        room = Room(
            room_create_user=USER_A,
            deck_id=uuid.UUID(deck["id"]),
            room_name="使用中",
        )
        db.add(room)
        db.commit()
        room_id = room.id

    assert client.delete(f"/deck/{deck['id']}/").status_code == 409
    assert client.get(f"/deck/{deck['id']}/").status_code == 200

    # ルームが無くなれば、削除できる
    with session_factory() as db:
        db.delete(db.get(Room, room_id))
        db.commit()
    assert client.delete(f"/deck/{deck['id']}/").status_code == 204


def test_list_decks_returns_only_own(client, session_factory):
    create(client, {"deck_name": "自分のデッキ"})
    login_as(USER_B)
    create(client, {"deck_name": "他人のデッキ"})
    login_as(USER_A)

    r = client.get("/deck/")
    assert r.status_code == 200
    names = [d["deck_name"] for d in r.json()]
    assert names == ["自分のデッキ"]


def test_list_decks_card_count(client, session_factory):
    deck = create(client).json()
    with session_factory() as db:
        card1 = Card(content="お題1")
        card2 = Card(content="お題2")
        db.add_all([card1, card2])
        db.flush()
        db.add(DeckCard(deck_id=uuid.UUID(deck["id"]), card_id=card1.id))
        db.add(DeckCard(deck_id=uuid.UUID(deck["id"]), card_id=card2.id))
        db.commit()

    r = client.get("/deck/")
    assert r.status_code == 200
    assert r.json()[0]["card_count"] == 2


def test_list_decks_card_count_zero_when_empty(client):
    create(client)
    r = client.get("/deck/")
    assert r.json()[0]["card_count"] == 0


@pytest.mark.parametrize(
    "method, path",
    [
        ("post", "/deck/"),
        ("get", "/deck/"),
        ("get", f"/deck/{uuid.uuid4()}/"),
        ("delete", f"/deck/{uuid.uuid4()}/"),
    ],
)
def test_all_routes_require_login(client, method, path):
    del api.dependency_overrides[get_current_user_id]
    r = client.request(method, path, json=BODY)
    assert r.status_code == 401
