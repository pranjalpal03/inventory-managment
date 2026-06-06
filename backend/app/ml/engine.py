"""14-day demand forecast engine using Linear Regression and WMA fallback."""

from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_utc_date(value: Any) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return ts.normalize()


def sales_to_daily_series(
    sales: list[dict[str, Any]], lookback_days: int = 90
) -> pd.Series:
    """Aggregate sale records into a daily quantity time series."""
    end = _utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=lookback_days - 1)
    date_index = pd.date_range(start=start, end=end, freq="D", tz=timezone.utc)

    if not sales:
        return pd.Series(0.0, index=date_index)

    rows: list[dict[str, Any]] = []
    for sale in sales:
        rows.append(
            {
                "date": _to_utc_date(sale["sale_date"]),
                "quantity": sale["quantity_sold"],
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.Series(0.0, index=date_index)

    daily = df.groupby("date")["quantity"].sum()
    daily.index = pd.DatetimeIndex(daily.index).tz_convert(timezone.utc)
    return daily.reindex(date_index, fill_value=0).astype(float)


def weighted_moving_average(daily: pd.Series, window: int = 7) -> float:
    """7-day weighted moving average (recent days weighted higher)."""
    recent = daily.tail(window)
    if recent.empty or recent.sum() == 0:
        return 0.0
    weights = np.arange(1, len(recent) + 1, dtype=float)
    return float(np.average(recent.values, weights=weights))


def forecast_demand(
    sales: list[dict[str, Any]],
    horizon_days: int = 14,
    lookback_days: int = 90,
) -> dict[str, Any]:
    """
    Project aggregate demand for the upcoming `horizon_days`.

    Uses Linear Regression over daily sales; falls back to 7-day WMA when
    insufficient history exists.
    """
    daily = sales_to_daily_series(sales, lookback_days=lookback_days)
    total_history = float(daily.sum())
    avg_daily = float(daily.mean()) if len(daily) else 0.0
    wma_daily = weighted_moving_average(daily)

    method = "linear_regression"
    daily_forecast = avg_daily

    non_zero_days = int((daily > 0).sum())
    if non_zero_days >= 7:
        x = np.arange(len(daily)).reshape(-1, 1)
        y = daily.values
        model = LinearRegression()
        model.fit(x, y)
        future_x = np.arange(len(daily), len(daily) + horizon_days).reshape(-1, 1)
        predictions = model.predict(future_x)
        daily_forecast = float(max(0.0, predictions.mean()))
    elif wma_daily > 0:
        method = "weighted_moving_average"
        daily_forecast = wma_daily
    elif avg_daily > 0:
        method = "historical_average"
        daily_forecast = avg_daily

    d_horizon = daily_forecast * horizon_days

    future_dates = [
        (daily.index[-1] + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        for i in range(horizon_days)
    ]
    daily_predictions = [
        {"date": future_dates[i], "predicted_quantity": round(daily_forecast, 2)}
        for i in range(horizon_days)
    ]

    historical = [
        {"date": idx.strftime("%Y-%m-%d"), "quantity": float(val)}
        for idx, val in daily.items()
    ]

    return {
        "average_daily_sales": round(avg_daily, 2),
        "weighted_moving_average_daily": round(wma_daily, 2),
        "forecast_horizon_days": horizon_days,
        "forecast_total_demand": round(d_horizon, 2),
        "forecast_method": method,
        "historical_daily": historical[-30:],
        "predicted_daily": daily_predictions,
        "total_historical_units": int(total_history),
    }
