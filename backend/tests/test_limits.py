"""1人あたりの上限(409)のテスト。

確認していること:
- 上限の数字が、API設計.mdに書いた値になっている
- 上限までは作れて、超えると409(デッキ、デッキ内のお題、作るお題、
  作るルーム、ルームの参加者)
- 上限は人ごとに数える。他の人の分や、公式のお題、参加しただけのルームは数えない
- 参加済みの人の再入室は、満員でも通る

確認していないこと:
- 本当の上限(300件など)まで作ること。テストでは数字を小さく差し替えている
- 同時に操作したときに、少し超えること(ゆるい上限として許容している)
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import limits
from app.core.security import get_current_user_id
from app.db.base import Base
from app.db.session import get_db
from app.main import app as api
from app.models import Card, Deck

USER_A = uuid.uuid4()
USER_B = uuid.uuid4()
USER_C = uuid.uuid4()


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


def make_deck(session_factory, owner_id):
    with session_factory() as db:
        deck = Deck(create_user_id=owner_id, deck_name="デッキ")
        db.add(deck)
        db.commit()
        return deck.id


def make_official_cards(session_factory, count):
    with session_factory() as db:
        cards = [Card(content=f"公式{i}") for i in range(count)]
        db.add_all(cards)
        db.commit()
        return [c.id for c in cards]


def test_limit_values():
    assert limits.MAX_DECKS_PER_USER == 20
    assert limits.MAX_CARDS_PER_DECK == 300
    assert limits.MAX_CARDS_PER_USER == 200
    assert limits.MAX_ROOMS_PER_USER == 4
    assert limits.MAX_USERS_PER_ROOM == 50


def test_deck_limit(client, monkeypatch):
    monkeypatch.setattr(limits, "MAX_DECKS_PER_USER", 2)
    body = {"deck_name": "デッキ"}
    assert client.post("/deck/", json=body).status_code == 201
    assert client.post("/deck/", json=body).status_code == 201
    assert client.post("/deck/", json=body).status_code == 409

    login_as(USER_B)  # 他の人は、まだ作れる
    assert client.post("/deck/", json=body).status_code == 201


def test_deck_limit_frees_up_after_delete(client, monkeypatch):
    monkeypatch.setattr(limits, "MAX_DECKS_PER_USER", 1)
    body = {"deck_name": "デッキ"}
    deck = client.post("/deck/", json=body).json()
    assert client.post("/deck/", json=body).status_code == 409
    client.delete(f"/deck/{deck['id']}/")
    assert client.post("/deck/", json=body).status_code == 201


def test_cards_per_deck_limit(client, session_factory, monkeypatch):
    monkeypatch.setattr(limits, "MAX_CARDS_PER_DECK", 2)
    card_ids = make_official_cards(session_factory, 3)
    deck_id = make_deck(session_factory, USER_A)
    other_deck_id = make_deck(session_factory, USER_A)

    def add(deck, card_id):
        body = {"card_id": str(card_id)}
        return client.post(f"/deck/{deck}/cards/", json=body).status_code

    assert add(deck_id, card_ids[0]) == 201
    assert add(deck_id, card_ids[1]) == 201
    assert add(deck_id, card_ids[2]) == 409
    # 別のデッキは、別に数える
    assert add(other_deck_id, card_ids[2]) == 201


def test_cards_per_user_limit(client, session_factory, monkeypatch):
    monkeypatch.setattr(limits, "MAX_CARDS_PER_USER", 2)
    make_official_cards(session_factory, 5)  # 公式は数えない
    body = {"content": "お題"}
    assert client.post("/card/", json=body).status_code == 201
    assert client.post("/card/", json=body).status_code == 201
    assert client.post("/card/", json=body).status_code == 409

    login_as(USER_B)
    assert client.post("/card/", json=body).status_code == 201


def test_rooms_per_user_limit(client, session_factory, monkeypatch):
    monkeypatch.setattr(limits, "MAX_ROOMS_PER_USER", 2)
    deck_a = make_deck(session_factory, USER_A)
    deck_b = make_deck(session_factory, USER_B)

    def create_room(deck_id):
        body = {"deck_id": str(deck_id), "room_name": "部屋"}
        return client.post("/room/", json=body)

    # Bが作ったルームに、Aが参加しても、Aの上限には数えない
    login_as(USER_B)
    room_of_b = create_room(deck_b).json()
    login_as(USER_A)
    client.post(f"/room/{room_of_b['id']}/user/")

    assert create_room(deck_a).status_code == 201
    assert create_room(deck_a).status_code == 201
    assert create_room(deck_a).status_code == 409

    login_as(USER_B)  # Bは自分の2つ目を作れる
    assert create_room(deck_b).status_code == 201


def test_room_participants_limit(client, session_factory, monkeypatch):
    monkeypatch.setattr(limits, "MAX_USERS_PER_ROOM", 2)
    deck_id = make_deck(session_factory, USER_A)
    body = {"deck_id": str(deck_id), "room_name": "部屋"}
    room_id = client.post("/room/", json=body).json()["id"]  # 作成者で1人目

    login_as(USER_B)
    assert client.post(f"/room/{room_id}/user/").status_code == 201  # 2人目
    login_as(USER_C)
    assert client.post(f"/room/{room_id}/user/").status_code == 409  # 満員

    login_as(USER_B)  # 参加済みのBは、満員でも再入室できる
    assert client.post(f"/room/{room_id}/user/").status_code == 200
