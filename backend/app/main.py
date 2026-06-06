"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.dependencies import get_current_user
from app.auth.security import hash_password
from app.config import get_settings
from app.database import (
    close_mongo_connection,
    connect_to_mongo,
    get_products_collection,
    get_sales_collection,
    get_users_collection,
)
from app.routes import analytics, auth, products, sales

logger = logging.getLogger(__name__)

ADMIN_USER_ID = "admin-demo-user"


async def migrate_legacy_user_scoping() -> None:
    """Assign orphaned records (pre-isolation) to the demo admin account."""
    products_col = await get_products_collection()
    sales_col = await get_sales_collection()

    product_result = await products_col.update_many(
        {"user_id": {"$exists": False}},
        {"$set": {"user_id": ADMIN_USER_ID}},
    )
    sales_result = await sales_col.update_many(
        {"user_id": {"$exists": False}},
        {"$set": {"user_id": ADMIN_USER_ID}},
    )
    if product_result.modified_count or sales_result.modified_count:
        logger.info(
            "Migrated legacy data to admin: %d products, %d sales",
            product_result.modified_count,
            sales_result.modified_count,
        )


async def seed_demo_data() -> None:
    """Populate demo inventory and sales for the admin account only."""
    products_col = await get_products_collection()
    count = await products_col.count_documents({"user_id": ADMIN_USER_ID})
    if count > 0:
        return

    now = datetime.now(timezone.utc)
    demo_products = [
        {
            "user_id": ADMIN_USER_ID,
            "phone_model": "iPhone 15 Pro",
            "design_name": "Midnight Blue",
            "category": "Clear Case",
            "current_stock": 8,
            "safety_stock": 15,
            "cost_price": 4.50,
            "selling_price": 19.99,
            "supplier_lead_time_days": 7,
            "created_at": now,
            "updated_at": now,
        },
        {
            "user_id": ADMIN_USER_ID,
            "phone_model": "Samsung Galaxy S24",
            "design_name": "Carbon Fiber",
            "category": "Rugged",
            "current_stock": 45,
            "safety_stock": 10,
            "cost_price": 5.25,
            "selling_price": 24.99,
            "supplier_lead_time_days": 5,
            "created_at": now,
            "updated_at": now,
        },
        {
            "user_id": ADMIN_USER_ID,
            "phone_model": "Google Pixel 8",
            "design_name": "Floral Bloom",
            "category": "Slim",
            "current_stock": 3,
            "safety_stock": 8,
            "cost_price": 3.80,
            "selling_price": 17.99,
            "supplier_lead_time_days": 10,
            "created_at": now,
            "updated_at": now,
        },
        {
            "user_id": ADMIN_USER_ID,
            "phone_model": "iPhone 14",
            "design_name": "Matte Black",
            "category": "Clear Case",
            "current_stock": 120,
            "safety_stock": 20,
            "cost_price": 3.50,
            "selling_price": 14.99,
            "supplier_lead_time_days": 7,
            "created_at": now,
            "updated_at": now,
        },
        {
            "user_id": ADMIN_USER_ID,
            "phone_model": "OnePlus 12",
            "design_name": "Neon Wave",
            "category": "Designer",
            "current_stock": 22,
            "safety_stock": 12,
            "cost_price": 4.00,
            "selling_price": 18.99,
            "supplier_lead_time_days": 6,
            "created_at": now,
            "updated_at": now,
        },
    ]

    result = await products_col.insert_many(demo_products)
    sales_col = await get_sales_collection()

    sales_seed: list[dict] = []
    for idx, inserted_id in enumerate(result.inserted_ids):
        pid = str(inserted_id)
        price = demo_products[idx]["selling_price"]
        base_day = now - timedelta(days=28)
        for day_offset in range(28):
            qty = [2, 3, 1, 4, 2, 0, 1, 3, 2, 5, 1, 2, 3, 4, 2, 1, 3, 2, 4, 1, 2, 3, 5, 2, 1, 4, 3, 2][
                day_offset
            ]
            if idx == 3 and day_offset > 20:
                qty = 0
            if qty > 0:
                sales_seed.append(
                    {
                        "user_id": ADMIN_USER_ID,
                        "product_id": pid,
                        "quantity_sold": qty + (idx % 2),
                        "total_revenue": round((qty + (idx % 2)) * price, 2),
                        "sale_date": base_day + timedelta(days=day_offset),
                    }
                )

    if sales_seed:
        await sales_col.insert_many(sales_seed)

    logger.info(
        "Seeded %d demo products and %d sales for admin user",
        len(demo_products),
        len(sales_seed),
    )


async def seed_demo_admin() -> None:
    """Ensure the default admin account exists."""
    settings = get_settings()
    users_col = await get_users_collection()
    now = datetime.now(timezone.utc)
    await users_col.update_one(
        {"email": settings.demo_admin_email.lower()},
        {
            "$setOnInsert": {
                "_id": ADMIN_USER_ID,
                "email": settings.demo_admin_email.lower(),
                "full_name": settings.demo_admin_name,
                "password_hash": hash_password(settings.demo_admin_password),
                "role": "admin",
                "created_at": now,
            }
        },
        upsert=True,
    )
    logger.info("Demo admin ready: %s", settings.demo_admin_email)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await connect_to_mongo(settings)
    await seed_demo_admin()
    await migrate_legacy_user_scoping()
    await seed_demo_data()
    logger.info("Connected to MongoDB: %s", settings.mongodb_db_name)
    yield
    await close_mongo_connection()
    logger.info("MongoDB connection closed")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(
        products.router, dependencies=[Depends(get_current_user)]
    )
    app.include_router(sales.router, dependencies=[Depends(get_current_user)])
    app.include_router(
        analytics.router, dependencies=[Depends(get_current_user)]
    )

    @app.get("/api/health")
    async def health_check() -> dict:
        return {"status": "ok", "version": settings.app_version}

    return app


app = create_app()
