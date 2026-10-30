"""ユーザーを消したときのテスト(DBの外部キーの決まり)。

確認していること:
- ユーザーを消すと、そのユーザーが作ったお題も消える(公式のお題として残らない)
- 公式のお題と、他のユーザーのお題は消えない
- 「ひとりで引く」のルームが残っていても、ユーザーを消せる
  (ルーム、デッキ、引いた記録が一緒に消える)

確認していないこと:
- 本物のDB(Postgres)。ここではSQLiteで外部キーを有効にして、
  モデルに書いた決まりを確かめる。0004のSQLそのものは確かめていない
"""
import uuid

import pytest
from sqlalchemy import create_engine, delete, event, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
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


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLiteは、そのままだと外部キーの決まりを守らないので、有効にする
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine, autoflush=False)() as session:
        session.add_all(
            [
                User(id=USER_A, user_name="A"),
                User(id=USER_B, user_name="B"),
            ]
        )
        session.commit()
        yield session


def delete_user(db, user_id):
    # APIを通さず、DBで直接消す(Supabaseの画面から消すのと同じ)
    db.execute(delete(User).where(User.id == user_id))
    db.commit()


def count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def test_user_cards_are_deleted_with_user(db):
    db.add_all(
        [
            Card(content="公式のお題"),
            Card(content="Aのお題", create_user_id=USER_A),
            Card(content="Bのお題", create_user_id=USER_B),
        ]
    )
    db.commit()

    delete_user(db, USER_A)
    contents = set(db.scalars(select(Card.content)))
    assert contents == {"公式のお題", "Bのお題"}


def test_user_with_solo_room_can_be_deleted(db):
    card = Card(content="Aのお題", create_user_id=USER_A)
    deck = Deck(create_user_id=USER_A, deck_name="デッキ")
    db.add_all([card, deck])
    db.flush()
    room = Room(room_create_user=USER_A, deck_id=deck.id, room_name="ひとりで引く")
    db.add_all([DeckCard(deck_id=deck.id, card_id=card.id), room])
    db.flush()
    db.add_all(
        [
            RoomUser(room_id=room.id, user_id=USER_A),
            RoomDrawnCard(room_id=room.id, card_id=card.id),
        ]
    )
    db.commit()

    delete_user(db, USER_A)
    for model in (Card, Deck, DeckCard, Room, RoomUser, RoomDrawnCard):
        assert count(db, model) == 0
