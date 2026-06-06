import { NavLink, useNavigate } from "react-router-dom";
import { BarChart3, LayoutDashboard, LogOut, Package, TrendingUp } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/inventory", label: "Inventory", icon: Package },
  { to: "/predictions", label: "Predictions", icon: TrendingUp },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-slate-800 bg-slate-900/80 backdrop-blur">
      <div className="flex items-center gap-3 border-b border-slate-800 px-6 py-5">
        <div className="rounded-lg bg-indigo-600 p-2">
          <BarChart3 className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-semibold text-white">Smart Inventory</p>
          <p className="text-xs text-slate-400">Phone Cases HQ</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                isActive
                  ? "bg-indigo-600/20 text-indigo-300"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-slate-800 p-4">
        {user && (
          <div className="mb-3">
            <p className="truncate text-sm font-medium text-white">{user.full_name}</p>
            <p className="truncate text-xs text-slate-500">{user.email}</p>
            <span className="mt-1 inline-block rounded-full bg-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-400">
              {user.role}
            </span>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-400 transition hover:bg-slate-800 hover:text-rose-300"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
