import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  accent?: "indigo" | "emerald" | "amber" | "rose";
}

const accentMap = {
  indigo: "bg-indigo-600/20 text-indigo-400",
  emerald: "bg-emerald-600/20 text-emerald-400",
  amber: "bg-amber-600/20 text-amber-400",
  rose: "bg-rose-600/20 text-rose-400",
};

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  accent = "indigo",
}: StatCardProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg shadow-black/20">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400">{title}</p>
          <p className="mt-2 text-2xl font-bold text-white">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
        </div>
        <div className={`rounded-lg p-2.5 ${accentMap[accent]}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}
