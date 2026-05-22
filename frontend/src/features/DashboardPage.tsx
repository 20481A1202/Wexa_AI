import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { api } from "../api/client";
import { MetricCard } from "../components/MetricCard";
import { WidgetChart } from "../components/WidgetChart";
import type { Dashboard, WidgetType } from "../types/models";

export function DashboardPage() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [presentation, setPresentation] = useState(false);
  const { data: dashboards = [] } = useQuery({ queryKey: ["dashboards"], queryFn: api.dashboards });
  const selected = useMemo<Dashboard | undefined>(
    () => dashboards.find((dashboard) => dashboard.id === (selectedId ?? dashboards[0]?.id)),
    [dashboards, selectedId]
  );

  const createDashboard = useMutation({
    mutationFn: api.createDashboard,
    onSuccess: (dashboard) => {
      setSelectedId(dashboard.id);
      queryClient.invalidateQueries({ queryKey: ["dashboards"] });
    }
  });
  const createWidget = useMutation({
    mutationFn: (payload: { dashboardId: string; title: string; widget_type: WidgetType; metric_name: string; time_range: string }) =>
      api.createWidget(payload.dashboardId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dashboards"] })
  });

  function onCreateDashboard(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    createDashboard.mutate({
      name: String(data.get("name")),
      description: String(data.get("description") || ""),
      is_public: data.get("is_public") === "on"
    });
    event.currentTarget.reset();
  }

  function onCreateWidget(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const data = new FormData(event.currentTarget);
    createWidget.mutate({
      dashboardId: selected.id,
      title: String(data.get("title")),
      widget_type: String(data.get("widget_type")) as WidgetType,
      metric_name: String(data.get("metric_name")),
      time_range: String(data.get("time_range"))
    });
    event.currentTarget.reset();
  }

  function createTemplate(kind: "web" | "sales" | "devops") {
    const labels = {
      web: ["Web Analytics", "Page Views", "page_view"],
      sales: ["Sales", "Checkouts", "checkout"],
      devops: ["DevOps", "Errors", "error"]
    }[kind];
    createDashboard.mutate(
      { name: labels[0], description: `${labels[0]} dashboard template`, is_public: false },
      {
        onSuccess: (dashboard) =>
          createWidget.mutate({
            dashboardId: dashboard.id,
            title: labels[1],
            widget_type: "line",
            metric_name: labels[2],
            time_range: "24h"
          })
      }
    );
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-3 sm:grid-cols-3">
        <MetricCard label="Dashboards" value={String(dashboards.length)} tone="mint" />
        <MetricCard label="Widgets" value={String(dashboards.reduce((sum, item) => sum + item.widgets.length, 0))} tone="ocean" />
        <MetricCard label="Public links" value={String(dashboards.filter((item) => item.is_public).length)} tone="amber" />
      </section>

      <section className={`grid gap-6 ${presentation ? "" : "xl:grid-cols-[320px_1fr]"}`}>
        {!presentation && (
        <aside className="space-y-4">
          <div className="rounded border border-slate-200 bg-white p-4">
            <h2 className="font-semibold text-ink">Templates</h2>
            <div className="mt-3 grid gap-2">
              <button className="focus-ring rounded border px-3 py-2 text-left text-sm" onClick={() => createTemplate("web")}>Web Analytics</button>
              <button className="focus-ring rounded border px-3 py-2 text-left text-sm" onClick={() => createTemplate("sales")}>Sales</button>
              <button className="focus-ring rounded border px-3 py-2 text-left text-sm" onClick={() => createTemplate("devops")}>DevOps</button>
            </div>
          </div>
          <form onSubmit={onCreateDashboard} className="rounded border border-slate-200 bg-white p-4">
            <h2 className="font-semibold text-ink">New dashboard</h2>
            <input name="name" required placeholder="Dashboard name" className="focus-ring mt-4 w-full rounded border px-3 py-2" />
            <textarea name="description" placeholder="Description" className="focus-ring mt-3 w-full rounded border px-3 py-2" />
            <label className="mt-3 flex items-center gap-2 text-sm text-slate-700">
              <input name="is_public" type="checkbox" />
              Public read-only link
            </label>
            <button className="focus-ring mt-4 flex w-full items-center justify-center gap-2 rounded bg-ink px-3 py-2 text-white">
              <Plus size={16} />
              Create
            </button>
          </form>

          <div className="rounded border border-slate-200 bg-white p-2">
            {dashboards.map((dashboard) => (
              <button
                key={dashboard.id}
                className={`focus-ring w-full rounded px-3 py-3 text-left ${
                  selected?.id === dashboard.id ? "bg-mint text-white" : "hover:bg-slate-100"
                }`}
                onClick={() => setSelectedId(dashboard.id)}
              >
                <span className="block font-medium">{dashboard.name}</span>
                <span className="text-xs opacity-80">{dashboard.widgets.length} widgets</span>
              </button>
            ))}
          </div>
        </aside>
        )}

        <section className="space-y-4">
          {selected ? (
            <>
              <div className="flex flex-col justify-between gap-3 rounded border border-slate-200 bg-white p-4 sm:flex-row sm:items-center">
                <div>
                  <h2 className="text-xl font-semibold text-ink">{selected.name}</h2>
                  <p className="text-sm text-slate-500">{selected.description || "No description"}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-slate-500">{selected.public_token ? `Public: ${selected.public_token}` : "Team only"}</span>
                  <button className="focus-ring rounded border px-3 py-2 text-sm" onClick={() => setPresentation(!presentation)}>
                    {presentation ? "Exit full screen" : "Present"}
                  </button>
                </div>
              </div>

              {!presentation && (
              <form onSubmit={onCreateWidget} className="grid gap-3 rounded border border-slate-200 bg-white p-4 md:grid-cols-5">
                <input name="title" required placeholder="Widget title" className="focus-ring rounded border px-3 py-2" />
                <select name="widget_type" className="focus-ring rounded border px-3 py-2" defaultValue="line">
                  <option value="line">Line</option>
                  <option value="bar">Bar</option>
                  <option value="pie">Pie</option>
                  <option value="kpi">KPI</option>
                  <option value="table">Table</option>
                </select>
                <input name="metric_name" required placeholder="Event name" className="focus-ring rounded border px-3 py-2" />
                <select name="time_range" className="focus-ring rounded border px-3 py-2" defaultValue="24h">
                  <option value="1h">1 hour</option>
                  <option value="24h">24 hours</option>
                  <option value="7d">7 days</option>
                  <option value="30d">30 days</option>
                </select>
                <button className="focus-ring rounded bg-mint px-3 py-2 font-medium text-white">Add widget</button>
              </form>
              )}

              <div className="grid gap-4 xl:grid-cols-2">
                {selected.widgets.map((widget) => (
                  <WidgetChart key={widget.id} dashboardId={selected.id} widget={widget} />
                ))}
              </div>
            </>
          ) : (
            <div className="grid min-h-96 place-items-center rounded border border-dashed border-slate-300 bg-white text-slate-500">
              Create a dashboard to begin.
            </div>
          )}
        </section>
      </section>
    </div>
  );
}
