"""ルームの状態(/room/{room_id}/state/)のテスト。

確認していること:
- ルーム情報・参加者・残り枚数・引いたお題が、API設計どおりの形で1回で返る
- ルーム情報は、GET /room/{id}/ と同じ内容
- 参加者はuser_nameつきで、参加が早い順。引いたお題は、引いた順でcontentつき
- remaining_card_countは、引くと減り、リセットすると元に戻る
- まだ引かれていないお題の中身は、レスポンスのどこにも出てこない(ネタバレ防止)
- 参加者以外は403、存在しないルームは404、ログインが無いと401

確認していないこと:
- 本物のDB(Postgres)での動作。ここではメモリ上のSQLiteを使う
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
from app.models import (
    Card,
    Deck,
    DeckCard,
    Room,
    RoomDrawnCard,
    RoomUser,
    User,
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


@pytest.fixture
def room_id(session_factory):
    """お題3枚のデッキを使うルームを作る。参加者はA、Bの順。"""
    with session_factory() as db:
        deck = Deck(create_user_id=USER_A, deck_name="デッキ")
        db.add_all(
            [
                deck,
                User(id=USER_A, user_name="Aさん"),
                User(id=USER_B, user_name="Bさん"),
            ]
        )
        db.flush()
        for i in range(3):
            card = Card(content=f"お題{i}", description=f"補足{i}")
            db.add(card)
            db.flush()
            db.add(DeckCard(deck_id=deck.id, card_id=card.id))
        room = Room(
            room_create_user=USER_A, deck_id=deck.id, room_name="部屋"
        )
        db.add(room)
        db.flush()
        db.add_all(
            [
                RoomUser(
                    room_id=room.id,
                    user_id=USER_B,
                    joined_at=OLD_TIME + timedelta(hours=1),
                    last_seen_at=OLD_TIME,
                ),
                RoomUser(
                    room_id=room.id,
                    user_id=USER_A,
                    joined_at=OLD_TIME,
                    last_seen_at=OLD_TIME,
                ),
            ]
        )
        db.commit()
        return room.id


def get_state(client, room_id):
    return client.get(f"/room/{room_id}/state/")


def test_state_shape_and_content(client, room_id, session_factory):
    # 「お題0」「お題1」を、この順で引いた状態にする
    with session_factory() as db:
        cards = db.query(Card).order_by(Card.content).limit(2).all()
        for i, card in enumerate(cards):
            db.add(
                RoomDrawnCard(
                    room_id=room_id,
                    card_id=card.id,
                    drawn_at=OLD_TIME + timedelta(minutes=i),
                )
            )
        db.commit()

    r = get_state(client, room_id)
    assert r.status_code == 200
    state = r.json()
    assert set(state) == {
        "room",
        "participants",
        "remaining_card_count",
        "drawn",
    }
    assert state["room"] == client.get(f"/room/{room_id}/").json()

    participants = state["participants"]
    assert [p["user_name"] for p in participants] == ["Aさん", "Bさん"]
    assert set(participants[0]) == {
        "user_id",
        "user_name",
        "joined_at",
        "last_seen_at",
    }

    drawn = state["drawn"]
    assert [d["content"] for d in drawn] == ["お題0", "お題1"]
    assert drawn[0]["description"] == "補足0"
    assert set(drawn[0]) == {"card_id", "content", "description", "drawn_at"}
    assert state["remaining_card_count"] == 1


def test_remaining_count_goes_down_and_resets(client, room_id):
    def remaining():
        return get_state(client, room_id).json()["remaining_card_count"]

    assert remaining() == 3
    client.post(f"/room/{room_id}/drawn/")
    assert remaining() == 2
    client.post(f"/room/{room_id}/drawn/")
    client.post(f"/room/{room_id}/drawn/")
    assert remaining() == 0
    client.delete(f"/room/{room_id}/drawn/")
    assert remaining() == 3


def test_undrawn_cards_are_not_leaked(client, room_id, session_factory):
    with session_factory() as db:
        drawn_card = db.query(Card).filter_by(content="お題0").one()
        db.add(RoomDrawnCard(room_id=room_id, card_id=drawn_card.id))
        db.commit()

    text = get_state(client, room_id).text
    assert "お題0" in text
    # 引かれていないお題の中身は、どこにも出てこない
    assert "お題1" not in text
    assert "お題2" not in text
    assert "補足1" not in text
    assert "補足2" not in text


def test_non_member_gets_403(client, room_id):
    login_as(OUTSIDER)
    assert get_state(client, room_id).status_code == 403


def test_unknown_room_is_404(client):
    assert get_state(client, uuid.uuid4()).status_code == 404


def test_requires_login(client, room_id):
    del api.dependency_overrides[get_current_user_id]
    assert get_state(client, room_id).status_code == 401
