import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { api } from "../api/client";
import type { Widget } from "../types/models";

export function WidgetChart({ dashboardId, widget, publicToken }: { dashboardId: string; widget: Widget; publicToken?: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["widget-data", dashboardId, widget.id, publicToken],
    queryFn: () => (publicToken ? api.publicWidgetData(publicToken, widget.id) : api.widgetData(dashboardId, widget.id)),
    refetchInterval: 30000
  });
  const points = data?.points ?? [];
  const total = points.reduce((sum, point) => sum + point.value, 0);

  return (
    <article className="rounded border border-slate-200 bg-white p-4">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-ink">{widget.title}</h3>
          <p className="text-sm text-slate-500">{widget.metric_name} · {widget.time_range}</p>
        </div>
        <span className="rounded bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">{widget.widget_type}</span>
      </div>
      {widget.widget_type === "table" ? (
        <div className="h-52 overflow-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-slate-500">
                <th className="py-2">Bucket</th>
                <th>Count</th>
              </tr>
            </thead>
            <tbody>
              {points.map((point) => (
                <tr key={point.label} className="border-b last:border-0">
                  <td className="py-2">{point.label}</td>
                  <td>{point.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : widget.widget_type === "kpi" ? (
        <div className="grid h-52 place-items-center text-5xl font-semibold text-mint">{total}</div>
      ) : isLoading ? (
        <div className="grid h-52 place-items-center text-sm text-slate-500">Loading data</div>
      ) : points.length === 0 ? (
        <div className="grid h-52 place-items-center text-sm text-slate-500">No events yet</div>
      ) : (
        <div className="h-52">
          <ResponsiveContainer width="100%" height="100%">
            {widget.widget_type === "bar" ? (
              <BarChart data={points}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" hide />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#0f766e" radius={[4, 4, 0, 0]} />
              </BarChart>
            ) : widget.widget_type === "pie" ? (
              <PieChart>
                <Tooltip />
                <Pie data={points} dataKey="value" nameKey="label" outerRadius={76}>
                  {points.map((point, index) => (
                    <Cell key={point.label} fill={["#0f766e", "#155e75", "#b45309", "#be123c"][index % 4]} />
                  ))}
                </Pie>
              </PieChart>
            ) : (
              <LineChart data={points}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" hide />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Line dataKey="value" stroke="#155e75" strokeWidth={2} dot={false} />
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>
      )}
    </article>
  );
}
