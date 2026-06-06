"""Pydantic schemas for user accounts."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: Annotated[str, Field(min_length=1, max_length=120)]


class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=6, max_length=128)]


class UserLogin(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=1, max_length=128)]


class UserInDB(BaseModel):
    """MongoDB user document — `password_hash` is never returned via API."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    email: EmailStr
    password_hash: str
    full_name: str = ""
    role: Literal["admin", "staff"] = "staff"
    created_at: datetime


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: Literal["admin", "staff"]
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
