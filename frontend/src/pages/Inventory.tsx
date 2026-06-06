import { FormEvent, useCallback, useEffect, useState } from "react";
import InventoryTable from "../components/InventoryTable";
import { api, type Prediction, type Product } from "../api";

const emptyForm = {
  phone_model: "",
  design_name: "",
  category: "Clear Case",
  current_stock: 0,
  safety_stock: 10,
  cost_price: 5,
  selling_price: 19.99,
  supplier_lead_time_days: 7,
};

export default function Inventory() {
  const [products, setProducts] = useState<Product[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [prods, predsRes] = await Promise.all([
      api.getProducts(),
      api.getPredictions(),
    ]);
    setProducts(prods);
    setPredictions(predsRes.predictions);
  }, []);

  useEffect(() => {
    load().catch((err) =>
      setMessage(err instanceof Error ? err.message : "Load failed")
    );
  }, [load]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await api.createProduct(form);
      setForm(emptyForm);
      setMessage("Product added successfully");
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Create failed");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Inventory Management</h1>
        <p className="text-sm text-slate-400">Add and monitor phone case stock</p>
      </div>

      {message && (
        <div className="rounded-lg border border-slate-700 bg-slate-800/60 px-4 py-2 text-sm text-slate-300">
          {message}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="grid gap-4 rounded-xl border border-slate-800 bg-slate-900/60 p-5 sm:grid-cols-2 lg:grid-cols-4"
      >
        {(
          [
            ["phone_model", "Phone Model"],
            ["design_name", "Design Name"],
            ["category", "Category"],
          ] as const
        ).map(([key, label]) => (
          <label key={key} className="block text-sm">
            <span className="text-slate-400">{label}</span>
            <input
              required
              value={form[key]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-850 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
            />
          </label>
        ))}
        {(
          [
            ["current_stock", "Current Stock"],
            ["safety_stock", "Safety Stock"],
            ["cost_price", "Cost Price"],
            ["selling_price", "Selling Price"],
            ["supplier_lead_time_days", "Lead Time (days)"],
          ] as const
        ).map(([key, label]) => (
          <label key={key} className="block text-sm">
            <span className="text-slate-400">{label}</span>
            <input
              required
              type="number"
              step={key.includes("price") ? "0.01" : "1"}
              value={form[key]}
              onChange={(e) =>
                setForm({ ...form, [key]: Number(e.target.value) })
              }
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-850 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
            />
          </label>
        ))}
        <div className="flex items-end sm:col-span-2 lg:col-span-4">
          <button
            type="submit"
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
          >
            Add Product
          </button>
        </div>
      </form>

      <InventoryTable products={products} predictions={predictions} onRefresh={load} />
    </div>
  );
}
