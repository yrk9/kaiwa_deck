"""JWT検証(get_current_user_id)のテスト。

確認していること:
- 正しいトークンなら200で、トークンのsubがuser_idとして返る
- Authorizationヘッダーが無い、またはBearer形式でないなら401
- 次の不正なトークンはすべて401になる
  期限切れ / audience違い / issuer違い / 別の鍵で署名 /
  HS256へのすり替え(署名方式の偽装) / subが無い・UUIDでない / 壊れた文字列

確認していないこと:
- SupabaseのJWKS(公開鍵)の取得。ここでは偽の鍵に差し替えている
  (本物のトークンでの確認は手動で1回行った)
"""
import time
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core import security
from app.core.config import settings

ISSUER = f"{settings.supabase_url}/auth/v1"
USER_ID = uuid.uuid4()

_signing_key = ec.generate_private_key(ec.SECP256R1())
_other_key = ec.generate_private_key(ec.SECP256R1())


class _FakeJWKSClient:
    def get_signing_key_from_jwt(self, token):
        class _Key:
            key = _signing_key.public_key()

        return _Key()


@pytest.fixture(autouse=True)
def fake_jwks(monkeypatch):
    monkeypatch.setattr(security, "_jwks_client", lambda: _FakeJWKSClient())


app = FastAPI()


@app.get("/protected")
def protected(user_id: uuid.UUID = Depends(security.get_current_user_id)):
    return {"user_id": str(user_id)}


client = TestClient(app)


def make_token(
    *,
    key=_signing_key,
    alg="ES256",
    sub=None,
    aud="authenticated",
    iss=ISSUER,
    exp_delta=3600,
):
    claims = {
        "sub": str(sub or USER_ID),
        "aud": aud,
        "iss": iss,
        "exp": int(time.time()) + exp_delta,
    }
    return jwt.encode(claims, key, algorithm=alg)


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_valid_token_returns_user_id():
    r = client.get("/protected", headers=bearer(make_token()))
    assert r.status_code == 200
    assert r.json() == {"user_id": str(USER_ID)}


def test_missing_header_is_401():
    r = client.get("/protected")
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"


def test_non_bearer_scheme_is_401():
    r = client.get("/protected", headers={"Authorization": "Basic abc"})
    assert r.status_code == 401


@pytest.mark.parametrize(
    "token",
    [
        pytest.param(make_token(exp_delta=-10), id="expired"),
        pytest.param(make_token(aud="anon"), id="wrong-audience"),
        pytest.param(
            make_token(iss="https://evil.example/auth/v1"),
            id="wrong-issuer",
        ),
        pytest.param(make_token(key=_other_key), id="signed-by-other-key"),
        pytest.param(
            make_token(key="0123456789abcdef0123456789abcdef", alg="HS256"),
            id="hs256-algorithm-confusion",
        ),
        pytest.param(make_token(sub="not-a-uuid"), id="non-uuid-sub"),
        pytest.param("not.a.jwt", id="garbage"),
    ],
)
def test_invalid_tokens_are_401(token):
    r = client.get("/protected", headers=bearer(token))
    assert r.status_code == 401


def test_token_without_sub_is_401():
    claims = {
        "aud": "authenticated",
        "iss": ISSUER,
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(claims, _signing_key, algorithm="ES256")
    r = client.get("/protected", headers=bearer(token))
    assert r.status_code == 401
