"""Authentication routes — login, register, and session introspection."""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, hash_password, verify_password
from app.auth.user_utils import get_stored_password_hash
from app.database import get_users_collection
from app.models.user import TokenResponse, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _serialize_user(doc: dict) -> UserResponse:
    return UserResponse(
        id=str(doc["_id"]),
        email=doc["email"],
        full_name=doc.get("full_name", ""),
        role=doc.get("role", "staff"),
        created_at=doc["created_at"],
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate) -> TokenResponse:
    users = await get_users_collection()
    existing = await users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    now = datetime.now(timezone.utc)
    doc = {
        "_id": str(ObjectId()),
        "email": payload.email.lower(),
        "full_name": payload.full_name.strip(),
        "password_hash": hash_password(payload.password),
        "role": "staff",
        "created_at": now,
    }
    await users.insert_one(doc)

    user = _serialize_user(doc)
    token = create_access_token(
        subject=user.id, extra_claims={"email": user.email, "user_id": user.id}
    )
    return TokenResponse(access_token=token, user=user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin) -> TokenResponse:
    users = await get_users_collection()
    doc = await users.find_one({"email": payload.email.lower()})
    stored_hash = get_stored_password_hash(doc) if doc else None
    if doc is None or stored_hash is None or not verify_password(payload.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    user = _serialize_user(doc)
    token = create_access_token(
        subject=user.id, extra_claims={"email": user.email, "user_id": user.id}
    )
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user
