"""お題を引く・一覧・リセット(/room/{room_id}/drawn)のテスト。

確認していること:
- 引くと201で、ルームのデッキのお題が1枚返る(content, descriptionつき)
- 引き続けると、デッキの全部のお題が1回ずつ出る。尽きたら409。空のデッキも409
- 他のルームで引いたお題は、このルームの残りに影響しない
- 同時に同じお題を選んでぶつかっても、選び直して別のお題を引ける
- 一覧は引いた順で、contentつき
- リセットすると一覧が空になり、また全部引ける。参加者なら誰でもできる
- 引く・一覧・リセットとも、参加者以外は403、存在しないルームは404
- ログイン(トークン)が無いと401

確認していないこと:
- 本物のDB(Postgres)での動作と、本当の同時アクセス。ここではメモリ上の
  SQLiteを使い、ぶつかる場面は差し替えで再現している
"""
import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import get_current_user_id
from app.crud import drawn as drawn_crud
from app.db.base import Base
from app.db.session import get_db
from app.main import app as api
from app.models import (
    Card,
    Deck,
    DeckCard,
    Room,
    RoomDrawnCard,
    RoomUser,
)

USER_A = uuid.uuid4()
USER_B = uuid.uuid4()
OUTSIDER = uuid.uuid4()
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
    login_as(USER_A)
    yield TestClient(api)
    api.dependency_overrides.clear()


def make_room(session_factory, card_count=3, deck_id=None):
    """お題card_count枚のデッキと、AとBが参加したルームを作る。"""
    with session_factory() as db:
        if deck_id is None:
            deck = Deck(create_user_id=USER_A, deck_name="デッキ")
            db.add(deck)
            db.flush()
            deck_id = deck.id
            for i in range(card_count):
                card = Card(content=f"お題{i}", description=f"補足{i}")
                db.add(card)
                db.flush()
                db.add(DeckCard(deck_id=deck_id, card_id=card.id))
        room = Room(
            room_create_user=USER_A, deck_id=deck_id, room_name="部屋"
        )
        db.add(room)
        db.flush()
        db.add_all(
            [
                RoomUser(room_id=room.id, user_id=USER_A),
                RoomUser(room_id=room.id, user_id=USER_B),
            ]
        )
        db.commit()
        return room.id, deck_id


@pytest.fixture
def room(session_factory):
    room_id, deck_id = make_room(session_factory)
    return {"room_id": room_id, "deck_id": deck_id}


def draw(client, room_id):
    return client.post(f"/room/{room_id}/drawn/")


def test_draw_card(client, room):
    r = draw(client, room["room_id"])
    assert r.status_code == 201
    drawn = r.json()
    assert drawn["room_id"] == str(room["room_id"])
    assert drawn["content"].startswith("お題")
    assert drawn["description"].startswith("補足")
    assert drawn["drawn_at"]
    uuid.UUID(drawn["card_id"])


def test_draw_all_cards_once_then_409(client, room):
    results = [draw(client, room["room_id"]) for _ in range(3)]
    assert [r.status_code for r in results] == [201, 201, 201]
    assert len({r.json()["card_id"] for r in results}) == 3
    assert draw(client, room["room_id"]).status_code == 409


def test_draw_from_empty_deck_is_409(client, session_factory):
    room_id, _ = make_room(session_factory, card_count=0)
    assert draw(client, room_id).status_code == 409


def test_other_room_does_not_affect_remaining(client, session_factory, room):
    other_room_id, _ = make_room(session_factory, deck_id=room["deck_id"])
    for _ in range(3):
        assert draw(client, room["room_id"]).status_code == 201
    assert draw(client, room["room_id"]).status_code == 409
    # 同じデッキを使う別のルームは、まだ全部引ける
    assert draw(client, other_room_id).status_code == 201


def test_draw_retries_when_card_was_taken_at_the_same_time(
    session_factory, room, monkeypatch
):
    with session_factory() as db:
        taken_id = db.query(Card).first().id
    # 別の人が、先にこのお題を引いた状態にしておく
    with session_factory() as other:
        other.add(RoomDrawnCard(room_id=room["room_id"], card_id=taken_id))
        other.commit()

    real_pick = drawn_crud._pick_undrawn_card
    calls = []

    def pick_taken_card_first(db, target_room):
        calls.append(1)
        if len(calls) == 1:
            return db.get(Card, taken_id)  # 引かれ済みだと気づかず選んでしまう
        return real_pick(db, target_room)

    monkeypatch.setattr(
        drawn_crud, "_pick_undrawn_card", pick_taken_card_first
    )

    with session_factory() as db:
        result = drawn_crud.draw_card(db, db.get(Room, room["room_id"]))
        assert result is not None
        assert result[1].id != taken_id
    assert len(calls) == 2


def test_list_drawn_in_order_with_content(client, room, session_factory):
    # 登録の順番とは逆の時刻にして、引いた順になるか確かめる
    with session_factory() as db:
        first, second = db.query(Card).order_by(Card.content).limit(2).all()
        db.add_all(
            [
                RoomDrawnCard(
                    room_id=room["room_id"],
                    card_id=second.id,
                    drawn_at=OLD_TIME + timedelta(hours=1),
                ),
                RoomDrawnCard(
                    room_id=room["room_id"],
                    card_id=first.id,
                    drawn_at=OLD_TIME,
                ),
            ]
        )
        db.commit()

    r = client.get(f"/room/{room['room_id']}/drawn/")
    assert r.status_code == 200
    items = r.json()
    assert [i["content"] for i in items] == ["お題0", "お題1"]
    assert set(items[0]) == {
        "room_id",
        "card_id",
        "drawn_at",
        "content",
        "description",
    }


def test_list_drawn_is_empty_at_first(client, room):
    r = client.get(f"/room/{room['room_id']}/drawn/")
    assert r.status_code == 200
    assert r.json() == []


def test_any_member_can_reset_and_draw_again(client, room):
    for _ in range(3):
        draw(client, room["room_id"])
    login_as(USER_B)  # 引いたAではなく、Bがリセットする
    assert client.delete(f"/room/{room['room_id']}/drawn/").status_code == 204
    assert client.get(f"/room/{room['room_id']}/drawn/").json() == []
    for _ in range(3):
        assert draw(client, room["room_id"]).status_code == 201


def test_non_member_gets_403(client, room):
    login_as(OUTSIDER)
    room_id = room["room_id"]
    assert draw(client, room_id).status_code == 403
    assert client.get(f"/room/{room_id}/drawn/").status_code == 403
    assert client.delete(f"/room/{room_id}/drawn/").status_code == 403


@pytest.mark.parametrize("method", ["post", "get", "delete"])
def test_unknown_room_is_404(client, method):
    r = client.request(method, f"/room/{uuid.uuid4()}/drawn/")
    assert r.status_code == 404


@pytest.mark.parametrize("method", ["post", "get", "delete"])
def test_requires_login(client, room, method):
    del api.dependency_overrides[get_current_user_id]
    r = client.request(method, f"/room/{room['room_id']}/drawn/")
    assert r.status_code == 401
