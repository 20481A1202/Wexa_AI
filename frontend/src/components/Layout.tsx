import { BarChart3, Bell, DatabaseZap, FileText, LayoutDashboard, LogOut, Users } from "lucide-react";
import type { ReactNode } from "react";
import type { UserContext } from "../types/models";

export type View = "dashboards" | "ingestion" | "team" | "alerts" | "reports";

interface Props {
  user: UserContext;
  view: View;
  onView: (view: View) => void;
  onLogout: () => void;
  children: ReactNode;
}

const nav = [
  { id: "dashboards" as const, label: "Dashboards", icon: LayoutDashboard },
  { id: "ingestion" as const, label: "Ingestion", icon: DatabaseZap },
  { id: "team" as const, label: "Team", icon: Users },
  { id: "alerts" as const, label: "Alerts", icon: Bell },
  { id: "reports" as const, label: "Reports", icon: FileText }
];

export function Layout({ user, view, onView, onLogout, children }: Props) {
  return (
    <div className="min-h-screen bg-slate-100">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:block">
        <div className="flex h-16 items-center gap-3 border-b border-slate-200 px-5">
          <span className="grid h-9 w-9 place-items-center rounded bg-mint text-white">
            <BarChart3 size={20} />
          </span>
          <span className="font-semibold">Atlas Analytics</span>
        </div>
        <nav className="space-y-1 p-3">
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={`focus-ring flex w-full items-center gap-3 rounded px-3 py-2 text-left text-sm font-medium ${
                  view === item.id ? "bg-mint text-white" : "text-slate-700 hover:bg-slate-100"
                }`}
                onClick={() => onView(item.id)}
              >
                <Icon size={18} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-6">
          <div>
            <p className="text-sm font-medium text-slate-500">{user.organization_name}</p>
            <h1 className="text-lg font-semibold text-ink">{user.full_name}</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="rounded border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700">{user.role}</span>
            <button className="focus-ring rounded border border-slate-300 p-2 text-slate-700" onClick={onLogout} title="Log out">
              <LogOut size={18} />
            </button>
          </div>
        </header>
        <nav className="grid grid-cols-5 gap-1 border-b border-slate-200 bg-white p-2 lg:hidden">
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={`focus-ring flex min-h-12 flex-col items-center justify-center gap-1 rounded px-2 py-2 text-xs font-medium ${
                  view === item.id ? "bg-mint text-white" : "text-slate-700"
                }`}
                onClick={() => onView(item.id)}
              >
                <Icon size={17} />
                {item.label}
              </button>
            );
          })}
        </nav>
        <main className="px-4 py-6 sm:px-6">{children}</main>
      </div>
    </div>
  );
}
