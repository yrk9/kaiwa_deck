import logging
from functools import lru_cache
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.core.config import settings

logger = logging.getLogger(__name__)

# FastAPIの既定エラー(バージョンで401/403が変わる)に頼らず自前で401を返す
bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def _jwks_client() -> PyJWKClient:
    url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    return PyJWKClient(url)


def verify_access_token(token: str) -> UUID:
    # トークンのiss等を信用してJWKSの取得先を決めてはならない。取得先は設定値(SUPABASE_URL)に固定する
    signing_key = _jwks_client().get_signing_key_from_jwt(token)
    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256", "RS256"],
        audience="authenticated",
        issuer=f"{settings.supabase_url}/auth/v1",
        options={"require": ["exp", "sub"]},
    )
    return UUID(payload["sub"])


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UUID:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        return verify_access_token(credentials.credentials)
    except (jwt.PyJWTError, ValueError) as e:
        # 不正トークンと設定ミス(SUPABASE_URL誤り等)がどちらも401になるため、原因をログに残す
        logger.warning("JWT verification failed: %s: %s", type(e).__name__, e)
        raise unauthorized
