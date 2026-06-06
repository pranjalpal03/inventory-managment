"""Sales logging routes with per-user isolation and atomic stock deduction."""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.database import get_products_collection, get_sales_collection
from app.models.sale import SaleCreate, SaleResponse
from app.models.user import UserResponse

router = APIRouter(prefix="/api/sales", tags=["sales"])


def _user_filter(user_id: str) -> dict:
    return {"user_id": user_id}


def _serialize_sale(doc: dict) -> SaleResponse:
    return SaleResponse(
        id=str(doc["_id"]),
        product_id=doc["product_id"],
        quantity_sold=doc["quantity_sold"],
        total_revenue=doc["total_revenue"],
        sale_date=doc["sale_date"],
    )


@router.get("", response_model=list[SaleResponse])
async def list_sales(
    limit: int = 100,
    current_user: UserResponse = Depends(get_current_user),
) -> list[SaleResponse]:
    collection = await get_sales_collection()
    cursor = (
        collection.find(_user_filter(current_user.id))
        .sort("sale_date", -1)
        .limit(min(limit, 500))
    )
    docs = await cursor.to_list(length=min(limit, 500))
    return [_serialize_sale(doc) for doc in docs]


@router.post("", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    payload: SaleCreate,
    current_user: UserResponse = Depends(get_current_user),
) -> SaleResponse:
    if not ObjectId.is_valid(payload.product_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product id")

    sale_date = payload.sale_date or datetime.now(timezone.utc)
    if sale_date.tzinfo is None:
        sale_date = sale_date.replace(tzinfo=timezone.utc)

    products = await get_products_collection()
    product = await products.find_one(
        {"_id": ObjectId(payload.product_id), **_user_filter(current_user.id)}
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    if product["current_stock"] < payload.quantity_sold:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient stock. Available: {product['current_stock']}, "
                f"requested: {payload.quantity_sold}"
            ),
        )

    updated = await products.find_one_and_update(
        {
            "_id": ObjectId(payload.product_id),
            "user_id": current_user.id,
            "current_stock": {"$gte": payload.quantity_sold},
        },
        {
            "$inc": {"current_stock": -payload.quantity_sold},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
        return_document=True,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock deduction failed due to insufficient stock or concurrent update",
        )

    total_revenue = round(payload.quantity_sold * product["selling_price"], 2)
    sale_doc = {
        "user_id": current_user.id,
        "product_id": payload.product_id,
        "quantity_sold": payload.quantity_sold,
        "total_revenue": total_revenue,
        "sale_date": sale_date,
    }
    sales = await get_sales_collection()
    result = await sales.insert_one(sale_doc)
    sale_doc["_id"] = result.inserted_id

    return _serialize_sale(sale_doc)
