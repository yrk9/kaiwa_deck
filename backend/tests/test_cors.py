"""CORS(ブラウザからのAPI呼び出しの許可)のテスト。

確認していること:
- 許可したサイト(既定はhttp://localhost:3000)からの確認(preflight)は通り、
  Authorizationヘッダー付きのPOSTを許可する応答が返る
- 許可していないサイトからの確認は、拒否される
- 普通のリクエストの応答にも、許可したサイトの印(ヘッダー)が付く
- CORS_ORIGINSは、カンマ区切りで複数指定できる

確認していないこと:
- 本物のブラウザでの動作(curlと同じ確認を、テストで行っている)
"""
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app as api

ALLOWED = "http://localhost:3000"
PREFLIGHT = {
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "authorization,content-type",
}


@pytest.fixture
def client():
    return TestClient(api)


def test_preflight_from_allowed_origin_passes(client):
    r = client.options("/deck/", headers={"Origin": ALLOWED, **PREFLIGHT})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == ALLOWED
    assert "POST" in r.headers["access-control-allow-methods"]
    allowed_headers = r.headers["access-control-allow-headers"].lower()
    assert "authorization" in allowed_headers


def test_preflight_from_other_origin_is_rejected(client):
    headers = {"Origin": "http://evil.test", **PREFLIGHT}
    r = client.options("/deck/", headers=headers)
    assert r.status_code == 400
    assert "access-control-allow-origin" not in r.headers


def test_normal_response_has_allow_origin(client):
    r = client.get("/health", headers={"Origin": ALLOWED})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == ALLOWED


def test_other_origin_gets_no_allow_origin(client):
    r = client.get("/health", headers={"Origin": "http://evil.test"})
    assert "access-control-allow-origin" not in r.headers


def test_multiple_origins_are_split_by_comma():
    settings = Settings(
        supabase_url="x",
        database_url="y",
        cors_origins="http://a.test, http://b.test ,",
    )
    assert settings.cors_origin_list == ["http://a.test", "http://b.test"]
