import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, BarChart3, DollarSign, Package, TrendingDown } from "lucide-react";
import AnalyticsCharts from "../components/AnalyticsCharts";
import EmptyState from "../components/EmptyState";
import InventoryTable from "../components/InventoryTable";
import StatCard from "../components/StatCard";
import {
  api,
  isEmptyData,
  type Overview,
  type Prediction,
  type Product,
  type SalesByModel,
  type SalesHistory,
} from "../api";

export default function Dashboard() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [salesHistory, setSalesHistory] = useState<SalesHistory | null>(null);
  const [salesByModel, setSalesByModel] = useState<SalesByModel[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [ov, prods, predsRes, history, byModelRes] = await Promise.all([
        api.getOverview(),
        api.getProducts(),
        api.getPredictions(),
        api.getSalesHistory(),
        api.getSalesByModel(),
      ]);
      setOverview(ov);
      setProducts(prods);
      setPredictions(predsRes.predictions);
      setSalesHistory(history);
      setSalesByModel(byModelRes.charts);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const isEmpty =
    products.length === 0 ||
    (overview !== null && isEmptyData(overview.status));

  const criticalItems = predictions.filter(
    (p) => p.status === "STOCKOUT RISK" || p.status === "CRITICAL RESTOCK"
  );

  const hasChartData =
    salesHistory !== null &&
    !isEmptyData(salesHistory.status) &&
    (salesHistory.history.length > 0 || salesByModel.length > 0);

  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-6 text-rose-300">
        <p className="font-medium">Unable to connect to API</p>
        <p className="mt-1 text-sm">{error}</p>
        <p className="mt-2 text-xs text-rose-400/80">
          Ensure the backend is running on port 8000 and MongoDB is available.
        </p>
      </div>
    );
  }

  if (!overview || !salesHistory) {
    return <p className="text-slate-400">Loading dashboard...</p>;
  }

  if (isEmpty) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard Overview</h1>
          <p className="text-sm text-slate-400">
            Live inventory status and predictive analytics
          </p>
        </div>
        <EmptyState
          icon={BarChart3}
          title="Your dashboard is waiting for data"
          description={
            overview.message ??
            "Add phone case products to your inventory to unlock sales analytics, ML forecasts, and restock alerts."
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard Overview</h1>
        <p className="text-sm text-slate-400">
          Live inventory status and predictive analytics
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Total Products" value={overview.total_products} icon={Package} />
        <StatCard
          title="Stock Units"
          value={overview.total_stock_units}
          icon={Package}
          accent="emerald"
        />
        <StatCard
          title="30-Day Revenue"
          value={`$${overview.revenue_last_30_days.toLocaleString()}`}
          icon={DollarSign}
          accent="indigo"
        />
        <StatCard
          title="Inventory Value"
          value={`$${overview.total_inventory_value.toLocaleString()}`}
          subtitle="At cost"
          icon={TrendingDown}
          accent="amber"
        />
      </div>

      {criticalItems.length > 0 && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
          <div className="flex items-center gap-2 text-amber-300">
            <AlertTriangle className="h-5 w-5" />
            <h2 className="font-semibold">Critical Restock Warnings</h2>
          </div>
          <ul className="mt-3 space-y-2">
            {criticalItems.slice(0, 5).map((item) => (
              <li
                key={item.product_id}
                className="flex items-center justify-between text-sm"
              >
                <span className="text-slate-200">
                  {item.design_name}{" "}
                  <span className="text-slate-500">({item.phone_model})</span>
                </span>
                <span className="rounded-full bg-rose-500/20 px-2 py-0.5 text-xs text-rose-300">
                  {item.status} · Order {item.suggested_restock_quantity} units
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {hasChartData ? (
        <AnalyticsCharts salesHistory={salesHistory} salesByModel={salesByModel} />
      ) : (
        <EmptyState
          icon={BarChart3}
          title="No sales data yet"
          description={
            salesHistory.message ??
            "Log your first sale to see sales trajectory charts and ML demand forecasts."
          }
          actionLabel="Go to Inventory"
          actionTo="/inventory"
        />
      )}

      <div>
        <h2 className="mb-3 text-lg font-semibold text-white">Inventory Snapshot</h2>
        <InventoryTable
          products={products}
          predictions={predictions}
          onRefresh={load}
        />
      </div>
    </div>
  );
}
