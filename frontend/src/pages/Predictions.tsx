import { useEffect, useState } from "react";
import { TrendingUp } from "lucide-react";
import EmptyState from "../components/EmptyState";
import { api, isEmptyData, type DeadStockItem, type Prediction } from "../api";

export default function Predictions() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [deadStock, setDeadStock] = useState<DeadStockItem[]>([]);
  const [emptyMessage, setEmptyMessage] = useState<string | null>(null);
  const [isEmpty, setIsEmpty] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getPredictions(), api.getDeadStock()])
      .then(([predsRes, deadRes]) => {
        setIsEmpty(isEmptyData(predsRes.status));
        setEmptyMessage(predsRes.message ?? null);
        setPredictions(predsRes.predictions);
        setDeadStock(deadRes.items);
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load predictions")
      )
      .finally(() => setLoading(false));
  }, []);

  const statusColor: Record<string, string> = {
    "STOCKOUT RISK": "bg-rose-500/20 text-rose-300 ring-rose-500/30",
    "CRITICAL RESTOCK": "bg-amber-500/20 text-amber-300 ring-amber-500/30",
    SAFE: "bg-emerald-500/20 text-emerald-300 ring-emerald-500/30",
  };

  if (loading) {
    return <p className="text-slate-400">Loading predictions...</p>;
  }

  if (error) {
    return <p className="text-rose-400">{error}</p>;
  }

  if (isEmpty || predictions.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white">ML Restock Schedule</h1>
          <p className="text-sm text-slate-400">
            14-day demand forecast with ROP-based reorder recommendations
          </p>
        </div>
        <EmptyState
          icon={TrendingUp}
          title="No predictions available yet"
          description={
            emptyMessage ??
            "Add products to your inventory and record sales to generate ML-powered restock recommendations."
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">ML Restock Schedule</h1>
        <p className="text-sm text-slate-400">
          14-day demand forecast with ROP-based reorder recommendations
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-800 bg-slate-850 text-xs uppercase text-slate-400">
            <tr>
              <th className="px-4 py-3">Product</th>
              <th className="px-4 py-3">Avg Daily</th>
              <th className="px-4 py-3">D₁₄</th>
              <th className="px-4 py-3">ROP</th>
              <th className="px-4 py-3">Stock</th>
              <th className="px-4 py-3">Order Qty</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Method</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {predictions.map((p) => (
              <tr key={p.product_id} className="hover:bg-slate-800/40">
                <td className="px-4 py-3">
                  <p className="font-medium text-white">{p.design_name}</p>
                  <p className="text-xs text-slate-500">{p.phone_model}</p>
                </td>
                <td className="px-4 py-3 font-mono text-slate-300">
                  {p.average_daily_sales}
                </td>
                <td className="px-4 py-3 font-mono text-slate-300">
                  {p.forecast_14_day_demand}
                </td>
                <td className="px-4 py-3 font-mono text-slate-300">{p.reorder_point}</td>
                <td className="px-4 py-3 font-mono text-white">{p.current_stock}</td>
                <td className="px-4 py-3 font-mono text-indigo-300">
                  {p.suggested_restock_quantity}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${statusColor[p.status] ?? ""}`}
                  >
                    {p.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-slate-500">{p.forecast_method}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {deadStock.length > 0 && (
        <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-5">
          <h2 className="text-lg font-semibold text-white">Dead Stock Alert</h2>
          <p className="mb-4 text-sm text-slate-400">
            Products with stock but zero sales in the last 30 days
          </p>
          <ul className="space-y-2">
            {deadStock.map((item) => (
              <li
                key={item.product_id}
                className="flex justify-between rounded-lg bg-slate-850 px-4 py-2 text-sm"
              >
                <span>
                  {item.design_name}{" "}
                  <span className="text-slate-500">({item.phone_model})</span>
                </span>
                <span className="text-amber-300">
                  {item.current_stock} units · ${item.inventory_value} tied up
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
