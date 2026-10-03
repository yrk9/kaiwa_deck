"""デッキへのお題の追加・削除(/deck/{deck_id}/cards)のテスト。

確認していること:
- 追加(201)・削除(204)がAPI設計どおりの形で動く
- デッキの持ち主以外は追加・削除できない(403)。これはデッキ自体の
  アクセス制御(test_decks.py)と同じ規約
- 存在しないデッキ・存在しないお題を指定すると404
- 同じお題を同じデッキに2回追加すると409(重複登録はしない)
- デッキに入っていないお題を削除しようとすると404
- ログインしていないと401

確認していないこと:
- 本物のDB(Postgres)での動作。ここではメモリ上のSQLiteを使う
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
from app.models import Card, Deck

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
def deck_and_card(session_factory):
    with session_factory() as db:
        deck = Deck(create_user_id=USER_A, deck_name="テストデッキ")
        card = Card(content="お題")
        db.add_all([deck, card])
        db.commit()
        return deck.id, card.id


def test_add_card_to_deck(client, deck_and_card):
    deck_id, card_id = deck_and_card
    r = client.post(f"/deck/{deck_id}/cards/", json={"card_id": str(card_id)})
    assert r.status_code == 201
    assert r.json() == {"deck_id": str(deck_id), "card_id": str(card_id)}


def test_add_duplicate_card_is_409(client, deck_and_card):
    deck_id, card_id = deck_and_card
    body = {"card_id": str(card_id)}
    client.post(f"/deck/{deck_id}/cards/", json=body)
    r = client.post(f"/deck/{deck_id}/cards/", json=body)
    assert r.status_code == 409


def test_add_unknown_card_is_404(client, deck_and_card):
    deck_id, _ = deck_and_card
    body = {"card_id": str(uuid.uuid4())}
    assert client.post(f"/deck/{deck_id}/cards/", json=body).status_code == 404


def test_add_card_to_unknown_deck_is_404(client, deck_and_card):
    _, card_id = deck_and_card
    body = {"card_id": str(card_id)}
    path = f"/deck/{uuid.uuid4()}/cards/"
    assert client.post(path, json=body).status_code == 404


def test_other_user_cannot_add_card(client, deck_and_card):
    deck_id, card_id = deck_and_card
    login_as(USER_B)
    body = {"card_id": str(card_id)}
    assert client.post(f"/deck/{deck_id}/cards/", json=body).status_code == 403


def test_remove_card_from_deck(client, deck_and_card):
    deck_id, card_id = deck_and_card
    client.post(f"/deck/{deck_id}/cards/", json={"card_id": str(card_id)})
    r = client.delete(f"/deck/{deck_id}/cards/{card_id}/")
    assert r.status_code == 204
    # 削除後にもう一度削除しようとすると、もう無いので404になる
    r = client.delete(f"/deck/{deck_id}/cards/{card_id}/")
    assert r.status_code == 404


def test_remove_card_not_in_deck_is_404(client, deck_and_card):
    deck_id, card_id = deck_and_card
    r = client.delete(f"/deck/{deck_id}/cards/{card_id}/")
    assert r.status_code == 404


def test_other_user_cannot_remove_card(client, deck_and_card):
    deck_id, card_id = deck_and_card
    client.post(f"/deck/{deck_id}/cards/", json={"card_id": str(card_id)})
    login_as(USER_B)
    r = client.delete(f"/deck/{deck_id}/cards/{card_id}/")
    assert r.status_code == 403


@pytest.mark.parametrize(
    "method, path",
    [
        ("post", "/deck/{deck_id}/cards/"),
        ("delete", "/deck/{deck_id}/cards/{card_id}/"),
    ],
)
def test_requires_login(client, deck_and_card, method, path):
    deck_id, card_id = deck_and_card
    del api.dependency_overrides[get_current_user_id]
    url = path.format(deck_id=deck_id, card_id=card_id)
    r = client.request(method, url, json={"card_id": str(card_id)})
    assert r.status_code == 401
