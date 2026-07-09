"""Authentication routes — login, register, and session introspection."""

import asyncio
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
    import time
    t_start = time.perf_counter()
    
    t0 = time.perf_counter()
    users = await get_users_collection()
    t1 = time.perf_counter()
    existing = await users.find_one({"email": payload.email.lower()})
    t2 = time.perf_counter()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    t3 = time.perf_counter()
    pwd_hash = await asyncio.to_thread(hash_password, payload.password)
    t4 = time.perf_counter()
    
    now = datetime.now(timezone.utc)
    doc = {
        "_id": str(ObjectId()),
        "email": payload.email.lower(),
        "full_name": payload.full_name.strip(),
        "password_hash": pwd_hash,
        "role": "staff",
        "created_at": now,
    }
    
    t5 = time.perf_counter()
    await users.insert_one(doc)
    t6 = time.perf_counter()

    user = _serialize_user(doc)
    
    t7 = time.perf_counter()
    token = create_access_token(
        subject=user.id, extra_claims={"email": user.email, "user_id": user.id}
    )
    t8 = time.perf_counter()
    
    print(f"[Register Timing] DB Get Collection: {t1-t0:.4f}s | DB Find One: {t2-t1:.4f}s | Hash Password: {t4-t3:.4f}s | DB Insert: {t6-t5:.4f}s | Token Gen: {t8-t7:.4f}s | Total Register: {t8-t_start:.4f}s", flush=True)
    return TokenResponse(access_token=token, user=user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin) -> TokenResponse:
    import time
    t_start = time.perf_counter()
    
    t0 = time.perf_counter()
    users = await get_users_collection()
    t1 = time.perf_counter()
    doc = await users.find_one({"email": payload.email.lower()})
    t2 = time.perf_counter()
    
    stored_hash = get_stored_password_hash(doc) if doc else None
    
    t3 = time.perf_counter()
    valid = await asyncio.to_thread(verify_password, payload.password, stored_hash) if stored_hash else False
    t4 = time.perf_counter()
    
    if doc is None or stored_hash is None or not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    user = _serialize_user(doc)
    
    t5 = time.perf_counter()
    token = create_access_token(
        subject=user.id, extra_claims={"email": user.email, "user_id": user.id}
    )
    t6 = time.perf_counter()
    
    print(f"[Login Timing] DB Get Collection: {t1-t0:.4f}s | DB Find One: {t2-t1:.4f}s | Verify Password: {t4-t3:.4f}s | Token Gen: {t6-t5:.4f}s | Total Login: {t6-t_start:.4f}s", flush=True)
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user
