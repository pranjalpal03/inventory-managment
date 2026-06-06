"""ML insights, restock logic, and dashboard analytics — per-user scoped."""

from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.database import get_products_collection, get_sales_collection
from app.ml.engine import forecast_demand, sales_to_daily_series
from app.ml.inventory_rules import (
    build_restock_analysis,
    classify_stock_status,
    compute_reorder_point,
)
from app.models.user import UserResponse

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _user_filter(user_id: str) -> dict:
    return {"user_id": user_id}


def _empty_overview(message: str = "No data available. Add your first product to get started.") -> dict:
    return {
        "status": "empty",
        "message": message,
        "total_products": 0,
        "total_stock_units": 0,
        "total_inventory_value": 0.0,
        "revenue_last_30_days": 0.0,
        "critical_stockout_risk": 0,
        "restock_warnings": 0,
    }


def _empty_sales_history(message: str = "No sales data available yet.") -> dict:
    return {
        "status": "empty",
        "message": message,
        "history": [],
        "predictions": [],
        "forecast_total_demand": 0.0,
        "forecast_method": "none",
    }


async def _product_count(user_id: str) -> int:
    products_col = await get_products_collection()
    return await products_col.count_documents(_user_filter(user_id))


@router.get("/overview")
async def dashboard_overview(
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    product_count = await _product_count(current_user.id)
    if product_count == 0:
        return _empty_overview()

    settings = get_settings()
    products_col = await get_products_collection()
    sales_col = await get_sales_collection()
    user_id = current_user.id

    products = await products_col.find(_user_filter(user_id)).to_list(length=500)
    total_products = len(products)
    total_stock = sum(p["current_stock"] for p in products)
    total_inventory_value = sum(p["current_stock"] * p["cost_price"] for p in products)

    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_sales = await sales_col.find(
        {**_user_filter(user_id), "sale_date": {"$gte": thirty_days_ago}}
    ).to_list(length=5000)
    revenue_30d = sum(s["total_revenue"] for s in recent_sales)

    critical_count = 0
    warning_count = 0
    for product in products:
        pid = str(product["_id"])
        sales = await sales_col.find(
            {**_user_filter(user_id), "product_id": pid}
        ).to_list(length=5000)
        forecast = forecast_demand(sales, horizon_days=settings.forecast_horizon_days)
        rop = compute_reorder_point(
            forecast["average_daily_sales"],
            product["supplier_lead_time_days"],
            product["safety_stock"],
        )
        status_label = classify_stock_status(
            product["current_stock"], product["safety_stock"], rop
        )
        if status_label == "STOCKOUT RISK":
            critical_count += 1
        elif status_label == "CRITICAL RESTOCK":
            warning_count += 1

    return {
        "status": "ok",
        "total_products": total_products,
        "total_stock_units": total_stock,
        "total_inventory_value": round(total_inventory_value, 2),
        "revenue_last_30_days": round(revenue_30d, 2),
        "critical_stockout_risk": critical_count,
        "restock_warnings": warning_count,
    }


@router.get("/predictions")
async def restock_predictions(
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    product_count = await _product_count(current_user.id)
    if product_count == 0:
        return {
            "status": "empty",
            "message": "No products to forecast. Add inventory to generate predictions.",
            "predictions": [],
        }

    settings = get_settings()
    products_col = await get_products_collection()
    sales_col = await get_sales_collection()
    user_id = current_user.id
    products = await products_col.find(_user_filter(user_id)).to_list(length=500)

    results: list[dict] = []
    for product in products:
        pid = str(product["_id"])
        sales = await sales_col.find(
            {**_user_filter(user_id), "product_id": pid}
        ).to_list(length=5000)
        forecast = forecast_demand(sales, horizon_days=settings.forecast_horizon_days)
        analysis = build_restock_analysis(
            product_id=pid,
            phone_model=product["phone_model"],
            design_name=product["design_name"],
            current_stock=product["current_stock"],
            safety_stock=product["safety_stock"],
            supplier_lead_time_days=product["supplier_lead_time_days"],
            average_daily_sales=forecast["average_daily_sales"],
            forecast_14_day_demand=forecast["forecast_total_demand"],
        )
        results.append(
            {
                **analysis.__dict__,
                "forecast_method": forecast["forecast_method"],
                "predicted_daily": forecast["predicted_daily"],
            }
        )

    priority = {"STOCKOUT RISK": 0, "CRITICAL RESTOCK": 1, "SAFE": 2}
    results.sort(key=lambda r: (priority.get(r["status"], 3), -r["suggested_restock_quantity"]))
    return {"status": "ok", "predictions": results}


@router.get("/dead-stock")
async def dead_stock_report(
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    product_count = await _product_count(current_user.id)
    if product_count == 0:
        return {
            "status": "empty",
            "message": "No inventory data available.",
            "items": [],
        }

    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.dead_stock_lookback_days)
    products_col = await get_products_collection()
    sales_col = await get_sales_collection()
    user_id = current_user.id

    products = await products_col.find(
        {**_user_filter(user_id), "current_stock": {"$gt": 0}}
    ).to_list(length=500)
    dead: list[dict] = []

    for product in products:
        pid = str(product["_id"])
        recent_sale = await sales_col.find_one(
            {
                **_user_filter(user_id),
                "product_id": pid,
                "sale_date": {"$gte": cutoff},
            }
        )
        if recent_sale is None:
            dead.append(
                {
                    "product_id": pid,
                    "phone_model": product["phone_model"],
                    "design_name": product["design_name"],
                    "current_stock": product["current_stock"],
                    "inventory_value": round(
                        product["current_stock"] * product["cost_price"], 2
                    ),
                    "lookback_days": settings.dead_stock_lookback_days,
                }
            )

    return {"status": "ok", "items": dead}


@router.get("/sales-history")
async def sales_history(
    product_id: str | None = None,
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    product_count = await _product_count(current_user.id)
    if product_count == 0:
        return _empty_sales_history()

    settings = get_settings()
    sales_col = await get_sales_collection()
    user_id = current_user.id
    query: dict = _user_filter(user_id)

    if product_id:
        if not ObjectId.is_valid(product_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product id")
        products_col = await get_products_collection()
        owned = await products_col.find_one(
            {"_id": ObjectId(product_id), **_user_filter(user_id)}
        )
        if owned is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        query["product_id"] = product_id

    sales = await sales_col.find(query).sort("sale_date", 1).to_list(length=5000)

    if not sales:
        return _empty_sales_history("No sales recorded yet. Log a sale to see trends.")

    forecast = forecast_demand(sales, horizon_days=settings.forecast_horizon_days)
    daily = sales_to_daily_series(sales)
    chart_history = [
        {"date": idx.strftime("%Y-%m-%d"), "actual": float(val)}
        for idx, val in daily.tail(30).items()
    ]

    return {
        "status": "ok",
        "history": chart_history,
        "predictions": forecast["predicted_daily"],
        "forecast_total_demand": forecast["forecast_total_demand"],
        "forecast_method": forecast["forecast_method"],
    }


@router.get("/sales-by-model")
async def sales_by_phone_model(
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    product_count = await _product_count(current_user.id)
    if product_count == 0:
        return {
            "status": "empty",
            "message": "No sales data available.",
            "charts": [],
        }

    products_col = await get_products_collection()
    sales_col = await get_sales_collection()
    user_id = current_user.id

    products = await products_col.find(_user_filter(user_id)).to_list(length=500)
    product_map = {str(p["_id"]): p["phone_model"] for p in products}
    product_ids = list(product_map.keys())

    if not product_ids:
        return {"status": "empty", "message": "No sales data available.", "charts": []}

    pipeline = [
        {"$match": {**_user_filter(user_id), "product_id": {"$in": product_ids}}},
        {
            "$group": {
                "_id": "$product_id",
                "total_quantity": {"$sum": "$quantity_sold"},
                "total_revenue": {"$sum": "$total_revenue"},
            }
        },
    ]
    aggregated = await sales_col.aggregate(pipeline).to_list(length=500)

    by_model: dict[str, dict] = {}
    for row in aggregated:
        model = product_map.get(row["_id"], "Unknown")
        if model not in by_model:
            by_model[model] = {"phone_model": model, "quantity": 0, "revenue": 0.0}
        by_model[model]["quantity"] += row["total_quantity"]
        by_model[model]["revenue"] = round(
            by_model[model]["revenue"] + row["total_revenue"], 2
        )

    charts = sorted(by_model.values(), key=lambda x: x["quantity"], reverse=True)
    if not charts:
        return {
            "status": "empty",
            "message": "No sales recorded yet.",
            "charts": [],
        }

    return {"status": "ok", "charts": charts}
