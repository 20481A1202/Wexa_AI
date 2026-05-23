import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { WidgetChart } from "../components/WidgetChart";

export function PublicDashboardPage({ token }: { token: string }) {
  const { data: dashboard, isLoading, isError } = useQuery({
    queryKey: ["public-dashboard", token],
    queryFn: () => api.publicDashboard(token)
  });

  if (isLoading) return <div className="grid min-h-screen place-items-center bg-slate-100 text-slate-600">Loading dashboard</div>;

  if (isError || !dashboard) {
    return <div className="grid min-h-screen place-items-center bg-slate-100 text-slate-600">Dashboard link is unavailable</div>;
  }

  return (
    <main className="min-h-screen bg-slate-100 px-4 py-6 sm:px-8">
      <section className="mx-auto max-w-6xl space-y-5">
        <div className="rounded border border-slate-200 bg-white p-4">
          <p className="text-sm font-medium text-mint">Public dashboard</p>
          <h1 className="mt-1 text-2xl font-semibold text-ink">{dashboard.name}</h1>
          <p className="text-sm text-slate-500">{dashboard.description || "Read-only analytics view"}</p>
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          {dashboard.widgets.map((widget) => (
            <WidgetChart key={widget.id} dashboardId={dashboard.id} widget={widget} publicToken={token} />
          ))}
        </div>
      </section>
    </main>
  );
}
