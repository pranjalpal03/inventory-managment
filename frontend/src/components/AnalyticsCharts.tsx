import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SalesByModel, SalesHistory } from "../api";

interface AnalyticsChartsProps {
  salesHistory: SalesHistory;
  salesByModel: SalesByModel[];
}

export default function AnalyticsCharts({
  salesHistory,
  salesByModel,
}: AnalyticsChartsProps) {
  if (salesHistory.history.length === 0 && salesByModel.length === 0) {
    return null;
  }

  const combined = salesHistory.history.map((h, i) => ({
    date: h.date.slice(5),
    actual: h.actual,
    predicted:
      salesHistory.predictions[i]?.predicted_quantity ??
      salesHistory.predictions[0]?.predicted_quantity ??
      0,
  }));

  const futureOnly = salesHistory.predictions.map((p) => ({
    date: p.date.slice(5),
    actual: null as number | null,
    predicted: p.predicted_quantity,
  }));

  const lastActual = combined[combined.length - 1];
  const trendData = [...combined, ...futureOnly.slice(combined.length > 0 ? 1 : 0)];
  if (lastActual && futureOnly.length > 0) {
    trendData[combined.length - 1] = {
      ...lastActual,
      predicted: lastActual.actual,
    };
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h3 className="mb-1 text-sm font-semibold text-white">
          Sales Trajectory & ML Forecast
        </h3>
        <p className="mb-4 text-xs text-slate-500">
          Method: {salesHistory.forecast_method} · 14-day demand:{" "}
          {salesHistory.forecast_total_demand} units
        </p>
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <YAxis yAxisId="left" tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                background: "#1e293b",
                border: "1px solid #334155",
                borderRadius: 8,
              }}
            />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="actual"
              stroke="#818cf8"
              strokeWidth={2}
              dot={false}
              name="Actual Sales"
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="predicted"
              stroke="#fbbf24"
              strokeWidth={2}
              strokeDasharray="6 4"
              dot={false}
              name="ML Forecast"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h3 className="mb-1 text-sm font-semibold text-white">
          Sales by Phone Model
        </h3>
        <p className="mb-4 text-xs text-slate-500">Units sold grouped by device</p>
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={salesByModel}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="phone_model"
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              interval={0}
              angle={-20}
              textAnchor="end"
              height={60}
            />
            <YAxis yAxisId="qty" tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <YAxis
              yAxisId="rev"
              orientation="right"
              tick={{ fill: "#94a3b8", fontSize: 11 }}
            />
            <Tooltip
              contentStyle={{
                background: "#1e293b",
                border: "1px solid #334155",
                borderRadius: 8,
              }}
            />
            <Legend />
            <Bar
              yAxisId="qty"
              dataKey="quantity"
              fill="#6366f1"
              name="Units Sold"
              radius={[4, 4, 0, 0]}
            />
            <Line
              yAxisId="rev"
              type="monotone"
              dataKey="revenue"
              stroke="#34d399"
              strokeWidth={2}
              name="Revenue ($)"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
