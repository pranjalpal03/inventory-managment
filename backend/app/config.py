"""Application configuration loaded from environment variables."""

from functools import lru_cache

from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized runtime configuration for the FastAPI backend."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.production"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(
        default="Smart Inventory Dashboard API",
        description="Display name for the FastAPI application.",
    )
    app_version: str = Field(default="1.0.0", description="Semantic API version.")
    debug: bool = Field(default=False, description="Enable verbose logging and docs.")

    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI (Motor async driver).",
    )

    @field_validator("mongodb_uri")
    @classmethod
    def validate_mongodb_uri(cls, value: str) -> str:
        uri = value.strip()
        placeholders = (
            "REPLACE_ATLAS",
            "<user>",
            "<password>",
            "<cluster>",
            "GENERATE_",
        )
        if any(token in uri for token in placeholders):
            raise ValueError(
                "MONGODB_URI contains placeholder values. "
                "Set a real MongoDB Atlas connection string in Render env vars."
            )
        if uri.startswith("mongodb+srv://") and "@" not in uri.split("mongodb+srv://", 1)[1]:
            raise ValueError("MONGODB_URI is missing username or password.")
        return uri
    mongodb_db_name: str = Field(
        default="smart_inventory",
        description="Target database name for inventory and sales collections.",
    )

    products_collection: str = Field(
        default="products",
        description="MongoDB collection for phone-case inventory records.",
    )
    sales_collection: str = Field(
        default="sales",
        description="MongoDB collection for sale transaction records.",
    )
    users_collection: str = Field(
        default="users",
        description="MongoDB collection for dashboard user accounts.",
    )

    jwt_secret: str = Field(
        default="change-me-in-production-use-a-long-random-secret",
        description="Secret key for signing JWT access tokens.",
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=480, description="Token lifetime in minutes.")

    demo_admin_email: str = Field(default="admin@inventory.com")
    demo_admin_password: str = Field(default="admin123")
    demo_admin_name: str = Field(default="Inventory Admin")

    cors_origins: Annotated[
        list[str],
        NoDecode,
        Field(
            default=["http://localhost:5173", "http://localhost:3000"],
            description="Allowed CORS origins for the React frontend.",
        ),
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    forecast_horizon_days: int = Field(
        default=14,
        description="Number of days to project demand in the ML forecast engine.",
    )
    dead_stock_lookback_days: int = Field(
        default=30,
        description="Window (days) with zero sales to classify dead stock.",
    )

    seed_demo_data: bool = Field(
        default=True,
        description="Seed sample products/sales on startup (disable in production).",
    )
    seed_demo_admin: bool = Field(
        default=True,
        description="Ensure demo admin account exists on startup.",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton per process)."""
    return Settings()
