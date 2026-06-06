"""Pydantic schemas for sale transaction documents."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SaleBase(BaseModel):
    """Shared fields for sale creation."""

    product_id: Annotated[
        str,
        Field(min_length=1, description="Reference to the sold product document id."),
    ]
    quantity_sold: Annotated[
        int,
        Field(gt=0, description="Number of units sold in this transaction."),
    ]
    sale_date: datetime | None = Field(
        default=None,
        description="Transaction timestamp (UTC). Defaults to server time if omitted.",
    )


class SaleCreate(SaleBase):
    """Schema for logging a new sale via POST /api/sales."""

    @field_validator("sale_date", mode="before")
    @classmethod
    def default_sale_date(cls, value: datetime | None) -> datetime | None:
        return value


class SaleInDB(BaseModel):
    """Full sale document as stored in MongoDB."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id", description="MongoDB document identifier.")
    user_id: str = Field(description="Owner account id — enforces per-user isolation.")
    product_id: str
    quantity_sold: int = Field(gt=0)
    total_revenue: float = Field(ge=0, description="quantity_sold × unit selling_price.")
    sale_date: datetime


class SaleResponse(BaseModel):
    """API response representation for a completed sale."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    quantity_sold: int
    total_revenue: float
    sale_date: datetime
