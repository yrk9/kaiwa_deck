"""お題API(/card)のテスト。

確認していること:
- 作成(201)・参照・更新・削除(204)が、API設計どおりの形で動く
- 更新と削除は作成者本人だけ。他人のお題や公式のお題は403
- 存在しないidは404、空や長すぎる入力は422
- ログイン(トークン)が無いと、どのルートも401

確認していないこと:
- 本物のDB(Postgres)での動作。ここではメモリ上のSQLiteを使うため、
  外部キー制約なども効かない
- JWT検証そのもの(test_security.pyで確認)
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
from app.models import Card

USER_A = uuid.uuid4()
USER_B = uuid.uuid4()
BODY = {"content": "最近ハマっていることは?", "description": "深掘りOK"}


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
    return client.post("/card/", json=body)


def test_create_card(client):
    r = create(client)
    assert r.status_code == 201
    card = r.json()
    assert card["create_user_id"] == str(USER_A)
    assert card["content"] == BODY["content"]
    assert card["description"] == BODY["description"]
    uuid.UUID(card["id"])


def test_create_card_without_description(client):
    r = create(client, {"content": "好きな食べ物は?"})
    assert r.status_code == 201
    assert r.json()["description"] is None


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({}, id="no-content"),
        pytest.param({"content": ""}, id="empty-content"),
        pytest.param({"content": "   "}, id="blank-content"),
        pytest.param({"content": "あ" * 201}, id="content-too-long"),
        pytest.param(
            {"content": "ok", "description": "あ" * 501},
            id="description-too-long",
        ),
    ],
)
def test_create_card_rejects_invalid_input(client, body):
    assert create(client, body).status_code == 422


def test_read_card(client):
    card = create(client).json()
    r = client.get(f"/card/{card['id']}/")
    assert r.status_code == 200
    assert r.json() == card


def test_read_card_of_other_user(client):
    card = create(client).json()
    login_as(USER_B)
    assert client.get(f"/card/{card['id']}/").status_code == 200


def test_read_unknown_card_is_404(client):
    assert client.get(f"/card/{uuid.uuid4()}/").status_code == 404


def test_owner_can_update(client):
    card = create(client).json()
    new = {"content": "休日は何をしていますか?", "description": None}
    r = client.put(f"/card/{card['id']}/", json=new)
    assert r.status_code == 200
    assert r.json()["content"] == new["content"]
    assert r.json()["description"] is None
    assert client.get(f"/card/{card['id']}/").json() == r.json()


def test_other_user_cannot_update(client):
    card = create(client).json()
    login_as(USER_B)
    r = client.put(f"/card/{card['id']}/", json={"content": "書き換え"})
    assert r.status_code == 403
    login_as(USER_A)
    assert client.get(f"/card/{card['id']}/").json() == card


def test_owner_can_delete(client):
    card = create(client).json()
    assert client.delete(f"/card/{card['id']}/").status_code == 204
    assert client.get(f"/card/{card['id']}/").status_code == 404


def test_other_user_cannot_delete(client):
    card = create(client).json()
    login_as(USER_B)
    assert client.delete(f"/card/{card['id']}/").status_code == 403
    login_as(USER_A)
    assert client.get(f"/card/{card['id']}/").status_code == 200


def test_official_card_cannot_be_changed(client, session_factory):
    with session_factory() as db:
        official = Card(content="公式のお題")
        db.add(official)
        db.commit()
        card_id = official.id
    assert client.put(f"/card/{card_id}/", json=BODY).status_code == 403
    assert client.delete(f"/card/{card_id}/").status_code == 403


@pytest.mark.parametrize("method", ["put", "delete"])
def test_change_unknown_card_is_404(client, method):
    r = client.request(method, f"/card/{uuid.uuid4()}/", json=BODY)
    assert r.status_code == 404


@pytest.mark.parametrize(
    "method, path",
    [
        ("post", "/card/"),
        ("get", f"/card/{uuid.uuid4()}/"),
        ("put", f"/card/{uuid.uuid4()}/"),
        ("delete", f"/card/{uuid.uuid4()}/"),
    ],
)
def test_all_routes_require_login(client, method, path):
    del api.dependency_overrides[get_current_user_id]
    r = client.request(method, path, json=BODY)
    assert r.status_code == 401
