import { api, getStockBadge, type Prediction, type Product } from "../api";

interface InventoryTableProps {
  products: Product[];
  predictions: Prediction[];
  onRefresh: () => void;
}

export default function InventoryTable({
  products,
  predictions,
  onRefresh,
}: InventoryTableProps) {
  const predictionMap = new Map(predictions.map((p) => [p.product_id, p]));

  const badgeStyles = {
    critical: "bg-rose-500/20 text-rose-300 ring-rose-500/30",
    warning: "bg-amber-500/20 text-amber-300 ring-amber-500/30",
    safe: "bg-emerald-500/20 text-emerald-300 ring-emerald-500/30",
  };

  async function handleSale(productId: string) {
    const qty = prompt("Quantity sold:");
    if (!qty || isNaN(Number(qty))) return;
    try {
      await api.recordSale(productId, Number(qty));
      onRefresh();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Sale failed");
    }
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-slate-800 bg-slate-850 text-xs uppercase text-slate-400">
          <tr>
            <th className="px-4 py-3">Product</th>
            <th className="px-4 py-3">Category</th>
            <th className="px-4 py-3">Stock</th>
            <th className="px-4 py-3">Safety</th>
            <th className="px-4 py-3">ROP</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {products.map((product) => {
            const pred = predictionMap.get(product.id);
            const rop = pred?.reorder_point ?? 0;
            const badge = getStockBadge(
              product.current_stock,
              product.safety_stock,
              rop
            );
            return (
              <tr key={product.id} className="hover:bg-slate-800/40">
                <td className="px-4 py-3">
                  <p className="font-medium text-white">{product.design_name}</p>
                  <p className="text-xs text-slate-500">{product.phone_model}</p>
                </td>
                <td className="px-4 py-3 text-slate-300">{product.category}</td>
                <td className="px-4 py-3 font-mono text-white">
                  {product.current_stock}
                </td>
                <td className="px-4 py-3 font-mono text-slate-400">
                  {product.safety_stock}
                </td>
                <td className="px-4 py-3 font-mono text-slate-400">{rop}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${badgeStyles[badge.variant]}`}
                  >
                    {badge.label}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => handleSale(product.id)}
                    className="rounded-md bg-indigo-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-indigo-500"
                  >
                    Log Sale
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
