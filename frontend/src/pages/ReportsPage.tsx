import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, FileClock } from "lucide-react";
import { api } from "../api/client";

export function ReportsPage() {
  const queryClient = useQueryClient();
  const [lastRun, setLastRun] = useState<string | null>(null);
  const { data: dashboards = [] } = useQuery({ queryKey: ["dashboards"], queryFn: api.dashboards });
  const { data: reports = [] } = useQuery({ queryKey: ["reports"], queryFn: api.reports });
  const createReport = useMutation({
    mutationFn: api.createReport,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["reports"] })
  });
  const runReport = useMutation({
    mutationFn: api.runReport,
    onSuccess: (run) => setLastRun(`http://localhost:8000${run.archive_url}`)
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    createReport.mutate({
      dashboard_id: String(data.get("dashboard_id")),
      name: String(data.get("name")),
      frequency: String(data.get("frequency")),
      recipients: String(data.get("recipients") || "")
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      snapshot_format: String(data.get("snapshot_format"))
    });
    event.currentTarget.reset();
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
      <section className="rounded border border-slate-200 bg-white p-4">
        <h2 className="text-xl font-semibold text-ink">Scheduled reports</h2>
        <div className="mt-4 grid gap-3">
          {reports.map((report) => (
            <article key={report.id} className="rounded border border-slate-200 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold">{report.name}</h3>
                  <p className="text-sm text-slate-500">
                    {report.frequency} · {report.snapshot_format.toUpperCase()} · {report.recipients.length} recipients
                  </p>
                </div>
                <button className="focus-ring flex items-center gap-2 rounded bg-ink px-3 py-2 text-sm text-white" onClick={() => runReport.mutate(report.id)}>
                  <FileClock size={16} />
                  Run
                </button>
              </div>
            </article>
          ))}
        </div>
        {lastRun && (
          <a className="mt-4 flex items-center gap-2 rounded bg-teal-50 px-3 py-2 text-sm font-medium text-mint" href={lastRun} target="_blank">
            <Download size={16} />
            Download latest generated PDF
          </a>
        )}
      </section>
      <form onSubmit={submit} className="rounded border border-slate-200 bg-white p-4">
        <h2 className="font-semibold text-ink">New report</h2>
        <select name="dashboard_id" required className="focus-ring mt-4 w-full rounded border px-3 py-2">
          <option value="">Select dashboard</option>
          {dashboards.map((dashboard) => (
            <option key={dashboard.id} value={dashboard.id}>{dashboard.name}</option>
          ))}
        </select>
        <input name="name" required placeholder="Report name" className="focus-ring mt-3 w-full rounded border px-3 py-2" />
        <select name="frequency" className="focus-ring mt-3 w-full rounded border px-3 py-2" defaultValue="daily">
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
        </select>
        <select name="snapshot_format" className="focus-ring mt-3 w-full rounded border px-3 py-2" defaultValue="pdf">
          <option value="pdf">PDF</option>
          <option value="png">PNG</option>
        </select>
        <textarea name="recipients" placeholder="Emails, comma separated" className="focus-ring mt-3 w-full rounded border px-3 py-2" />
        <button className="focus-ring mt-4 w-full rounded bg-mint px-3 py-2 text-white">Schedule report</button>
      </form>
    </div>
  );
}
