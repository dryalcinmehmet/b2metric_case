from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, UUID4, validator, EmailStr


class JwtTokenSchema(BaseModel):
    token: str
    payload: dict
    expire: datetime


class TokenPair(BaseModel):
    access: JwtTokenSchema
    refresh: JwtTokenSchema


class RefreshToken(BaseModel):
    refresh: str


class SuccessResponseScheme(BaseModel):
    msg: str


class JWTToken(BaseModel):
    id: UUID4
    expire: datetime

    class Config:
        from_attributes = True
