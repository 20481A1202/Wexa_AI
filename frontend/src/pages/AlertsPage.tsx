import { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing } from "lucide-react";
import { api } from "../api/client";

export function AlertsPage() {
  const queryClient = useQueryClient();
  const { data: alerts = [] } = useQuery({ queryKey: ["alerts"], queryFn: api.alerts });
  const { data: history = [] } = useQuery({ queryKey: ["alert-history"], queryFn: api.alertHistory });
  const { data: notifications = [] } = useQuery({ queryKey: ["notifications"], queryFn: api.notifications });
  const createAlert = useMutation({
    mutationFn: api.createAlert,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] })
  });
  const evaluate = useMutation({
    mutationFn: api.evaluateAlerts,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["alert-history"] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    }
  });
  const mute = useMutation({
    mutationFn: ({ alertId, minutes }: { alertId: string; minutes: number }) => api.muteAlert(alertId, minutes),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] })
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    createAlert.mutate({
      name: String(data.get("name")),
      metric_name: String(data.get("metric_name")),
      operator: String(data.get("operator")),
      threshold: Number(data.get("threshold")),
      window_minutes: Number(data.get("window_minutes")),
      email_recipients: String(data.get("email_recipients") || "")
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      webhook_url: String(data.get("webhook_url") || "") || null
    });
    event.currentTarget.reset();
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
      <section className="rounded border border-slate-200 bg-white p-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-xl font-semibold text-ink">Alert rules</h2>
          <button className="focus-ring rounded bg-ink px-3 py-2 text-sm text-white" onClick={() => evaluate.mutate()}>
            Evaluate now
          </button>
        </div>
        <div className="mt-4 grid gap-3">
          {alerts.map((alert) => (
            <article key={alert.id} className="rounded border border-slate-200 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold">{alert.name}</h3>
                  <p className="text-sm text-slate-500">
                    {alert.metric_name} {alert.operator} {alert.threshold} for {alert.window_minutes} minutes
                  </p>
                </div>
                <span className="rounded bg-slate-100 px-2 py-1 text-xs font-medium">{alert.status}</span>
              </div>
              <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
                {alert.email_recipients.length > 0 && <span>Email: {alert.email_recipients.join(", ")}</span>}
                {alert.webhook_url && <span>Webhook enabled</span>}
                {alert.muted_until && <span>Muted until {new Date(alert.muted_until).toLocaleString()}</span>}
              </div>
              <button className="focus-ring mt-3 rounded border px-3 py-2 text-sm" onClick={() => mute.mutate({ alertId: alert.id, minutes: 30 })}>
                Mute 30 min
              </button>
            </article>
          ))}
        </div>
        <h3 className="mt-6 font-semibold text-ink">History</h3>
        <div className="mt-3 space-y-2 text-sm">
          {history.length === 0 ? (
            <p className="text-slate-500">No alert history yet</p>
          ) : (
            history.map((item) => (
              <p key={item.id} className="rounded bg-slate-50 px-3 py-2">
                {item.status}: {item.message}
              </p>
            ))
          )}
        </div>
        <h3 className="mt-6 font-semibold text-ink">Notifications</h3>
        <div className="mt-3 space-y-2 text-sm">
          {notifications.length === 0 ? (
            <p className="text-slate-500">No notifications yet</p>
          ) : (
            notifications.map((item) => (
              <div key={item.id} className="rounded bg-slate-50 px-3 py-2">
                <p className="font-medium">{item.title}</p>
                <p>{item.channel} · {item.status}{item.recipient ? ` · ${item.recipient}` : ""}</p>
                {item.error && <p className="text-amber">{item.error}</p>}
              </div>
            ))
          )}
        </div>
      </section>
      <form onSubmit={submit} className="rounded border border-slate-200 bg-white p-4">
        <h2 className="font-semibold text-ink">New alert</h2>
        <input name="name" required placeholder="Name" className="focus-ring mt-4 w-full rounded border px-3 py-2" />
        <input name="metric_name" required placeholder="Event name" className="focus-ring mt-3 w-full rounded border px-3 py-2" />
        <div className="mt-3 grid grid-cols-3 gap-2">
          <select name="operator" className="focus-ring rounded border px-3 py-2" defaultValue=">">
            <option>&gt;</option>
            <option>&lt;</option>
            <option>=</option>
          </select>
          <input name="threshold" required type="number" placeholder="Limit" className="focus-ring rounded border px-3 py-2" />
          <input name="window_minutes" required type="number" defaultValue={10} className="focus-ring rounded border px-3 py-2" />
        </div>
        <textarea name="email_recipients" placeholder="Email recipients, comma separated" className="focus-ring mt-3 w-full rounded border px-3 py-2" />
        <input name="webhook_url" placeholder="Slack-compatible webhook URL" className="focus-ring mt-3 w-full rounded border px-3 py-2" />
        <button className="focus-ring mt-4 flex w-full items-center justify-center gap-2 rounded bg-mint px-3 py-2 text-white">
          <BellRing size={16} />
          Create alert
        </button>
      </form>
    </div>
  );
}
