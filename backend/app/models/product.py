"""Pydantic schemas for phone-case inventory (Product) documents."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductBase(BaseModel):
    """Shared fields for product create/update payloads."""

    phone_model: Annotated[
        str,
        Field(
            min_length=1,
            max_length=120,
            description="Target phone model (e.g. iPhone 15 Pro).",
        ),
    ]
    design_name: Annotated[
        str,
        Field(
            min_length=1,
            max_length=120,
            description="Visual design or SKU variant name.",
        ),
    ]
    category: Annotated[
        str,
        Field(
            min_length=1,
            max_length=80,
            description="Product category (e.g. Clear Case, Rugged).",
        ),
    ]
    current_stock: Annotated[
        int,
        Field(ge=0, description="Units currently available in warehouse."),
    ]
    safety_stock: Annotated[
        int,
        Field(ge=0, description="Minimum buffer before stockout risk."),
    ]
    cost_price: Annotated[
        float,
        Field(gt=0, description="Unit cost from supplier (USD)."),
    ]
    selling_price: Annotated[
        float,
        Field(gt=0, description="Unit retail price (USD)."),
    ]
    supplier_lead_time_days: Annotated[
        int,
        Field(ge=1, le=365, description="Days from order to delivery."),
    ]

    @field_validator("selling_price")
    @classmethod
    def selling_price_must_exceed_cost(cls, value: float, info) -> float:
        cost = info.data.get("cost_price")
        if cost is not None and value < cost:
            raise ValueError("selling_price must be greater than or equal to cost_price")
        return value


class ProductCreate(ProductBase):
    """Schema for creating a new inventory record."""


class ProductUpdate(BaseModel):
    """Partial update schema — all fields optional."""

    model_config = ConfigDict(extra="forbid")

    phone_model: str | None = Field(default=None, min_length=1, max_length=120)
    design_name: str | None = Field(default=None, min_length=1, max_length=120)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    current_stock: int | None = Field(default=None, ge=0)
    safety_stock: int | None = Field(default=None, ge=0)
    cost_price: float | None = Field(default=None, gt=0)
    selling_price: float | None = Field(default=None, gt=0)
    supplier_lead_time_days: int | None = Field(default=None, ge=1, le=365)


class ProductInDB(ProductBase):
    """Full product document as stored in MongoDB."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id", description="MongoDB document identifier.")
    user_id: str = Field(description="Owner account id — enforces per-user isolation.")
    created_at: datetime = Field(description="Record creation timestamp (UTC).")
    updated_at: datetime = Field(description="Last modification timestamp (UTC).")


class ProductResponse(ProductBase):
    """API response representation (uses `id` instead of MongoDB `_id`)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
