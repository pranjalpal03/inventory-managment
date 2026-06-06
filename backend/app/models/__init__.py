"""Pydantic schema definitions for MongoDB documents."""

from app.models.product import (
    ProductCreate,
    ProductInDB,
    ProductResponse,
    ProductUpdate,
)
from app.models.sale import SaleCreate, SaleInDB, SaleResponse

__all__ = [
    "ProductCreate",
    "ProductInDB",
    "ProductResponse",
    "ProductUpdate",
    "SaleCreate",
    "SaleInDB",
    "SaleResponse",
]
