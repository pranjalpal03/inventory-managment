import { getStoredToken } from "./context/AuthContext";

const API_BASE = (import.meta.env.VITE_API_BASE as string) || "/api";

function parseErrorDetail(body: unknown): string {
  if (!body || typeof body !== "object") return "Request failed";
  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (typeof first === "object" && first && "msg" in first) {
      return String((first as { msg: string }).msg);
    }
  }
  return "Request failed";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(parseErrorDetail(body) || `Request failed: ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "staff";
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface Product {
  id: string;
  phone_model: string;
  design_name: string;
  category: string;
  current_stock: number;
  safety_stock: number;
  cost_price: number;
  selling_price: number;
  supplier_lead_time_days: number;
  created_at: string;
  updated_at: string;
}

export type DataStatus = "ok" | "empty";

export interface Overview {
  status: DataStatus;
  message?: string;
  total_products: number;
  total_stock_units: number;
  total_inventory_value: number;
  revenue_last_30_days: number;
  critical_stockout_risk: number;
  restock_warnings: number;
}

export interface Prediction {
  product_id: string;
  phone_model: string;
  design_name: string;
  current_stock: number;
  safety_stock: number;
  supplier_lead_time_days: number;
  average_daily_sales: number;
  forecast_14_day_demand: number;
  reorder_point: number;
  suggested_restock_quantity: number;
  status: string;
  forecast_method: string;
  predicted_daily: { date: string; predicted_quantity: number }[];
}

export interface PredictionsResponse {
  status: DataStatus;
  message?: string;
  predictions: Prediction[];
}

export interface SalesHistory {
  status: DataStatus;
  message?: string;
  history: { date: string; actual: number }[];
  predictions: { date: string; predicted_quantity: number }[];
  forecast_total_demand: number;
  forecast_method: string;
}

export interface SalesByModel {
  phone_model: string;
  quantity: number;
  revenue: number;
}

export interface SalesByModelResponse {
  status: DataStatus;
  message?: string;
  charts: SalesByModel[];
}

export interface DeadStockItem {
  product_id: string;
  phone_model: string;
  design_name: string;
  current_stock: number;
  inventory_value: number;
  lookback_days: number;
}

export interface DeadStockResponse {
  status: DataStatus;
  message?: string;
  items: DeadStockItem[];
}

export const api = {
  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (full_name: string, email: string, password: string) =>
    request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ full_name, email, password }),
    }),
  getMe: (token?: string) =>
    request<AuthUser>("/auth/me", {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    }),
  getOverview: () => request<Overview>("/analytics/overview"),
  getProducts: () => request<Product[]>("/products"),
  getPredictions: () => request<PredictionsResponse>("/analytics/predictions"),
  getSalesHistory: () => request<SalesHistory>("/analytics/sales-history"),
  getSalesByModel: () => request<SalesByModelResponse>("/analytics/sales-by-model"),
  getDeadStock: () => request<DeadStockResponse>("/analytics/dead-stock"),
  createProduct: (data: Omit<Product, "id" | "created_at" | "updated_at">) =>
    request<Product>("/products", { method: "POST", body: JSON.stringify(data) }),
  updateProduct: (id: string, data: Partial<Product>) =>
    request<Product>(`/products/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteProduct: (id: string) =>
    request<void>(`/products/${id}`, { method: "DELETE" }),
  recordSale: (product_id: string, quantity_sold: number) =>
    request<{ id: string }>("/sales", {
      method: "POST",
      body: JSON.stringify({ product_id, quantity_sold }),
    }),
};

export type StockBadge = "critical" | "warning" | "safe";

export function getStockBadge(
  currentStock: number,
  safetyStock: number,
  reorderPoint: number
): { label: string; variant: StockBadge } {
  if (currentStock <= safetyStock) {
    return { label: "Stockout Risk", variant: "critical" };
  }
  if (currentStock <= reorderPoint) {
    return { label: "Restock Warning", variant: "warning" };
  }
  return { label: "Safe", variant: "safe" };
}

export function isEmptyData(status?: DataStatus): boolean {
  return status === "empty";
}
