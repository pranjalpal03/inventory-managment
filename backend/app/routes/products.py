"""CRUD routes for phone-case inventory — scoped per authenticated user."""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.auth.dependencies import get_current_user
from app.database import get_products_collection
from app.models.product import ProductCreate, ProductResponse, ProductUpdate
from app.models.user import UserResponse

router = APIRouter(prefix="/api/products", tags=["products"])


def _user_filter(user_id: str) -> dict:
    return {"user_id": user_id}


def _serialize_product(doc: dict) -> ProductResponse:
    return ProductResponse(
        id=str(doc["_id"]),
        phone_model=doc["phone_model"],
        design_name=doc["design_name"],
        category=doc["category"],
        current_stock=doc["current_stock"],
        safety_stock=doc["safety_stock"],
        cost_price=doc["cost_price"],
        selling_price=doc["selling_price"],
        supplier_lead_time_days=doc["supplier_lead_time_days"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


async def _get_owned_product(product_id: str, user_id: str) -> dict:
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product id")

    collection = await get_products_collection()
    doc = await collection.find_one({"_id": ObjectId(product_id), **_user_filter(user_id)})
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return doc


@router.get("", response_model=list[ProductResponse])
async def list_products(
    current_user: UserResponse = Depends(get_current_user),
) -> list[ProductResponse]:
    collection = await get_products_collection()
    cursor = collection.find(_user_filter(current_user.id)).sort("phone_model", 1)
    docs = await cursor.to_list(length=500)
    return [_serialize_product(doc) for doc in docs]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ProductResponse:
    doc = await _get_owned_product(product_id, current_user.id)
    return _serialize_product(doc)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    current_user: UserResponse = Depends(get_current_user),
) -> ProductResponse:
    now = datetime.now(timezone.utc)
    doc = {
        **payload.model_dump(),
        "user_id": current_user.id,
        "created_at": now,
        "updated_at": now,
    }
    collection = await get_products_collection()
    try:
        result = await collection.insert_one(doc)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product already exists",
        ) from exc

    doc["_id"] = result.inserted_id
    return _serialize_product(doc)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    payload: ProductUpdate,
    current_user: UserResponse = Depends(get_current_user),
) -> ProductResponse:
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    updates["updated_at"] = datetime.now(timezone.utc)
    collection = await get_products_collection()
    result = await collection.find_one_and_update(
        {"_id": ObjectId(product_id), **_user_filter(current_user.id)},
        {"$set": updates},
        return_document=True,
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return _serialize_product(result)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> None:
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product id")

    collection = await get_products_collection()
    result = await collection.delete_one(
        {"_id": ObjectId(product_id), **_user_filter(current_user.id)}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
