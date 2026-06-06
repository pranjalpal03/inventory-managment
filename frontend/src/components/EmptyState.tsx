import { LucideIcon, PackagePlus } from "lucide-react";
import { Link } from "react-router-dom";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  actionTo?: string;
}

export default function EmptyState({
  icon: Icon = PackagePlus,
  title,
  description,
  actionLabel = "Add your first product",
  actionTo = "/inventory",
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-900/40 px-6 py-16 text-center">
      <div className="mb-4 rounded-full bg-indigo-600/15 p-4">
        <Icon className="h-8 w-8 text-indigo-400" />
      </div>
      <h2 className="text-lg font-semibold text-white">{title}</h2>
      <p className="mt-2 max-w-md text-sm text-slate-400">{description}</p>
      {actionTo && (
        <Link
          to={actionTo}
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-indigo-500"
        >
          <PackagePlus className="h-4 w-4" />
          {actionLabel}
        </Link>
      )}
    </div>
  );
}
