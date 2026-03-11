from typing import Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel


class TokenPayload(BaseModel):
    sub: str
    role: Literal["admin", "user"]


security = HTTPBearer()


def decode_token(
    creds: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    import os

    jwt_secret = os.getenv("JWT_SECRET", "change_me")
    jwt_alg = os.getenv("JWT_ALG", "HS256")

    token = creds.credentials
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=[jwt_alg])
        return TokenPayload(**payload)
    except (JWTError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def require_admin(tp: TokenPayload = Depends(decode_token)) -> TokenPayload:
    if tp.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return tp