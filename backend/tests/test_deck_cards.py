"""デッキへのお題の追加・削除(/deck/{deck_id}/cards)のテスト。

確認していること:
- 一覧は、そのデッキに入っているお題だけが出る(空なら[])
- 一覧は、デッキに入れた順。入れた日時が同じお題どうしは、内容の順
- 一覧の各お題には、自分のメモだけが付く(他人のメモは出ず、無ければnull)
- 一覧の各お題のdeck_countは、そのお題が入っている自分のデッキの数(他人のデッキは数えない)
- 追加(201)・削除(204)がAPI設計どおりの形で動く
- デッキの持ち主以外は、一覧・追加・削除ができない(403)。これはデッキ自体の
  アクセス制御(test_decks.py)と同じ規約
- 追加できるのは、公式のお題と自分のお題だけ。他人のお題は403で、デッキにも入らない
- 存在しないデッキ・存在しないお題を指定すると404
- 同じお題を同じデッキに2回追加すると409(重複登録はしない)
- デッキに入っていないお題を削除しようとすると404
- ログインしていないと401

確認していないこと:
- 本物のDB(Postgres)での動作。ここではメモリ上のSQLiteを使う
"""
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import get_current_user_id
from app.db.base import Base
from app.db.session import get_db
from app.main import app as api
from app.models import Card, CardNote, Deck, DeckCard

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


def make_card(session_factory, owner_id):
    with session_factory() as db:
        card = Card(content="誰かのお題", create_user_id=owner_id)
        db.add(card)
        db.commit()
        return card.id


def test_list_cards_in_deck(client, deck_and_card, session_factory):
    deck_id, official_id = deck_and_card
    own_id = make_card(session_factory, USER_A)
    for card_id in (official_id, own_id):
        body = {"card_id": str(card_id)}
        client.post(f"/deck/{deck_id}/cards/", json=body)

    r = client.get(f"/deck/{deck_id}/cards/")
    assert r.status_code == 200
    items = r.json()
    assert {c["id"] for c in items} == {str(official_id), str(own_id)}
    assert set(items[0]) == {
        "id",
        "create_user_id",
        "content",
        "description",
        "category",
        "note",
        "deck_count",
    }


def test_deck_count_counts_only_own_decks(
    client, deck_and_card, session_factory
):
    deck_id, card_id = deck_and_card
    with session_factory() as db:
        own_deck = Deck(create_user_id=USER_A, deck_name="自分の別のデッキ")
        others_deck = Deck(create_user_id=USER_B, deck_name="他人のデッキ")
        db.add_all([own_deck, others_deck])
        db.flush()
        for deck in (deck_id, own_deck.id, others_deck.id):
            db.add(DeckCard(deck_id=deck, card_id=card_id))
        db.commit()

    items = client.get(f"/deck/{deck_id}/cards/").json()
    # このデッキと自分の別のデッキの2つ。他人のデッキは数えない
    assert items[0]["deck_count"] == 2


def test_list_is_in_added_order(client, deck_and_card, session_factory):
    deck_id, _ = deck_and_card
    # SQLiteの日時は秒までなので、入れた日時は手で決める
    added = [
        ("ん", datetime(2026, 1, 1, tzinfo=timezone.utc)),
        ("い", datetime(2026, 1, 1, tzinfo=timezone.utc)),
        ("あ", datetime(2026, 1, 2, tzinfo=timezone.utc)),
    ]
    with session_factory() as db:
        for content, added_at in added:
            card = Card(content=content)
            db.add(card)
            db.flush()
            db.add(
                DeckCard(deck_id=deck_id, card_id=card.id, added_at=added_at)
            )
        db.commit()

    items = client.get(f"/deck/{deck_id}/cards/").json()
    assert [c["content"] for c in items] == ["い", "ん", "あ"]


def test_list_has_only_own_note(client, deck_and_card, session_factory):
    deck_id, card_id = deck_and_card
    client.post(f"/deck/{deck_id}/cards/", json={"card_id": str(card_id)})
    with session_factory() as db:
        db.add(CardNote(user_id=USER_B, card_id=card_id, note="Bのメモ"))
        db.commit()

    # 他人のメモしか無いうちは、自分にはnull
    assert client.get(f"/deck/{deck_id}/cards/").json()[0]["note"] is None

    with session_factory() as db:
        db.add(CardNote(user_id=USER_A, card_id=card_id, note="Aのメモ"))
        db.commit()
    assert client.get(f"/deck/{deck_id}/cards/").json()[0]["note"] == "Aのメモ"


def test_list_excludes_cards_of_other_decks(
    client, deck_and_card, session_factory
):
    deck_id, card_id = deck_and_card
    client.post(f"/deck/{deck_id}/cards/", json={"card_id": str(card_id)})
    with session_factory() as db:
        other_deck = Deck(create_user_id=USER_A, deck_name="別のデッキ")
        other_card = Card(content="別のデッキのお題")
        db.add_all([other_deck, other_card])
        db.flush()
        db.add(DeckCard(deck_id=other_deck.id, card_id=other_card.id))
        db.commit()

    items = client.get(f"/deck/{deck_id}/cards/").json()
    assert [c["id"] for c in items] == [str(card_id)]


def test_list_is_empty_when_deck_has_no_cards(client, deck_and_card):
    deck_id, _ = deck_and_card
    r = client.get(f"/deck/{deck_id}/cards/")
    assert r.status_code == 200
    assert r.json() == []


def test_other_user_cannot_list_cards(client, deck_and_card):
    deck_id, _ = deck_and_card
    login_as(USER_B)
    assert client.get(f"/deck/{deck_id}/cards/").status_code == 403


def test_list_cards_of_unknown_deck_is_404(client):
    assert client.get(f"/deck/{uuid.uuid4()}/cards/").status_code == 404


def test_can_add_own_card(client, deck_and_card, session_factory):
    deck_id, _ = deck_and_card
    card_id = make_card(session_factory, USER_A)
    body = {"card_id": str(card_id)}
    assert client.post(f"/deck/{deck_id}/cards/", json=body).status_code == 201


def test_cannot_add_other_users_card(client, deck_and_card, session_factory):
    deck_id, _ = deck_and_card
    card_id = make_card(session_factory, USER_B)
    body = {"card_id": str(card_id)}
    assert client.post(f"/deck/{deck_id}/cards/", json=body).status_code == 403
    with session_factory() as db:
        key = {"deck_id": deck_id, "card_id": card_id}
        assert db.get(DeckCard, key) is None


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
        ("get", "/deck/{deck_id}/cards/"),
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
