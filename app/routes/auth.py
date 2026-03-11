from typing import Literal

from fastapi import APIRouter
from jose import jwt

from app.models.schemas import LoginOut
import os

router = APIRouter(prefix="/auth", tags=["Auth"])

JWT_SECRET = os.getenv("JWT_SECRET", "change_me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")


@router.post("/dev-token", response_model=LoginOut)
def dev_token(role: Literal["admin", "user"] = "admin"):
    payload = {"sub": "dev", "role": role}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    return {"token": token}