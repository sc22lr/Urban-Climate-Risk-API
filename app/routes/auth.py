from typing import Literal

from fastapi import APIRouter

from app.core.auth import create_token
from app.models.schemas import LoginOut

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/dev-token", response_model=LoginOut)
def dev_token(role: Literal["admin", "user"] = "admin"):
    payload = {"sub": "dev", "role": role}
    token = create_token(payload)
    return {"token": token}