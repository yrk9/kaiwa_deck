"""想定回答のメモ(/card/{card_id}/note)のテスト。

確認していること:
- 保存(200)がAPI設計どおりの形で返り、2回目の保存は新しい行を作らず上書きする
- メモは人ごと。同じお題でも、他の人のメモは変わらない
- 公式・自分・他人のどのお題にもメモを付けられる(お題の参照は誰でもできるため)
- 前後の空白は取り除く。空のメモや、2000文字を超えるメモは422
- 削除(204)は自分のメモだけが消え、メモが無いときは404
- 存在しないお題へのメモは404
- ログインしていないと401

確認していないこと:
- 本物のDB(Postgres)での動作。ここではメモリ上のSQLiteを使う
- 同時に保存したときの動き
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import get_current_user_id
from app.db.base import Base
from app.db.session import get_db
from app.main import app as api
from app.models import Card, CardNote

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


def make_card(session_factory, owner_id=None):
    with session_factory() as db:
        card = Card(content="志望動機は?", create_user_id=owner_id)
        db.add(card)
        db.commit()
        return card.id


def note_of(session_factory, user_id, card_id):
    with session_factory() as db:
        key = {"user_id": user_id, "card_id": card_id}
        card_note = db.get(CardNote, key)
        return None if card_note is None else card_note.note


def test_save_note(client, session_factory):
    card_id = make_card(session_factory)
    r = client.put(f"/card/{card_id}/note/", json={"note": "  人の役に立つ  "})
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"card_id", "note", "updated_at"}
    assert body["card_id"] == str(card_id)
    assert body["note"] == "人の役に立つ"


def test_second_save_overwrites(client, session_factory):
    card_id = make_card(session_factory)
    client.put(f"/card/{card_id}/note/", json={"note": "1回目"})
    r = client.put(f"/card/{card_id}/note/", json={"note": "2回目"})
    assert r.json()["note"] == "2回目"
    with session_factory() as db:
        count = db.execute(select(func.count()).select_from(CardNote))
        assert count.scalar_one() == 1


def test_notes_are_per_user(client, session_factory):
    card_id = make_card(session_factory)
    client.put(f"/card/{card_id}/note/", json={"note": "Aのメモ"})
    login_as(USER_B)
    client.put(f"/card/{card_id}/note/", json={"note": "Bのメモ"})
    assert note_of(session_factory, USER_A, card_id) == "Aのメモ"
    assert note_of(session_factory, USER_B, card_id) == "Bのメモ"


@pytest.mark.parametrize("owner_id", [None, USER_A, USER_B])
def test_can_note_any_card(client, session_factory, owner_id):
    card_id = make_card(session_factory, owner_id)
    r = client.put(f"/card/{card_id}/note/", json={"note": "メモ"})
    assert r.status_code == 200


@pytest.mark.parametrize("note", ["", "   ", "あ" * 2001])
def test_invalid_note_is_422(client, session_factory, note):
    card_id = make_card(session_factory)
    r = client.put(f"/card/{card_id}/note/", json={"note": note})
    assert r.status_code == 422


def test_save_note_on_unknown_card_is_404(client):
    r = client.put(f"/card/{uuid.uuid4()}/note/", json={"note": "メモ"})
    assert r.status_code == 404


def test_delete_note(client, session_factory):
    card_id = make_card(session_factory)
    client.put(f"/card/{card_id}/note/", json={"note": "メモ"})
    assert client.delete(f"/card/{card_id}/note/").status_code == 204
    assert note_of(session_factory, USER_A, card_id) is None
    # もう無いので、2回目は404
    assert client.delete(f"/card/{card_id}/note/").status_code == 404


def test_delete_removes_only_own_note(client, session_factory):
    card_id = make_card(session_factory)
    client.put(f"/card/{card_id}/note/", json={"note": "Aのメモ"})
    login_as(USER_B)
    # Bはメモを書いていないので、Aのメモがあっても404
    assert client.delete(f"/card/{card_id}/note/").status_code == 404
    assert note_of(session_factory, USER_A, card_id) == "Aのメモ"


@pytest.mark.parametrize("method", ["put", "delete"])
def test_requires_login(client, session_factory, method):
    card_id = make_card(session_factory)
    del api.dependency_overrides[get_current_user_id]
    r = client.request(method, f"/card/{card_id}/note/", json={"note": "x"})
    assert r.status_code == 401
