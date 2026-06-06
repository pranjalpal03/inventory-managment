"""Reorder point (ROP) and restock quantity calculations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RestockAnalysis:
    product_id: str
    phone_model: str
    design_name: str
    current_stock: int
    safety_stock: int
    supplier_lead_time_days: int
    average_daily_sales: float
    forecast_14_day_demand: float
    reorder_point: float
    suggested_restock_quantity: int
    status: str


def compute_reorder_point(
    average_daily_sales: float,
    supplier_lead_time_days: int,
    safety_stock: int,
) -> float:
    """ROP = (Average Daily Sales × Lead Time) + Safety Stock."""
    return (average_daily_sales * supplier_lead_time_days) + safety_stock


def compute_suggested_restock(
    forecast_14_day_demand: float,
    safety_stock: int,
    current_stock: int,
) -> int:
    """Suggested Restock = (D_14 + Safety Stock) − current_stock."""
    return max(0, int(round(forecast_14_day_demand + safety_stock - current_stock)))


def classify_stock_status(
    current_stock: int,
    safety_stock: int,
    reorder_point: float,
) -> str:
    if current_stock <= safety_stock:
        return "STOCKOUT RISK"
    if current_stock <= reorder_point:
        return "CRITICAL RESTOCK"
    return "SAFE"


def build_restock_analysis(
    product_id: str,
    phone_model: str,
    design_name: str,
    current_stock: int,
    safety_stock: int,
    supplier_lead_time_days: int,
    average_daily_sales: float,
    forecast_14_day_demand: float,
) -> RestockAnalysis:
    rop = compute_reorder_point(
        average_daily_sales, supplier_lead_time_days, safety_stock
    )
    suggested = compute_suggested_restock(
        forecast_14_day_demand, safety_stock, current_stock
    )
    status = classify_stock_status(current_stock, safety_stock, rop)
    return RestockAnalysis(
        product_id=product_id,
        phone_model=phone_model,
        design_name=design_name,
        current_stock=current_stock,
        safety_stock=safety_stock,
        supplier_lead_time_days=supplier_lead_time_days,
        average_daily_sales=round(average_daily_sales, 2),
        forecast_14_day_demand=round(forecast_14_day_demand, 2),
        reorder_point=round(rop, 2),
        suggested_restock_quantity=suggested,
        status=status,
    )
