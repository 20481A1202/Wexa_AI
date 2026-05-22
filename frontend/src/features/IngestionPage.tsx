import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, Send, Upload } from "lucide-react";
import { api, websocketUrl } from "../api/client";
import type { UserContext } from "../types/models";

export function IngestionPage({ user }: { user: UserContext }) {
  const queryClient = useQueryClient();
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [liveEvents, setLiveEvents] = useState<string[]>([]);
  const { data: keys = [] } = useQuery({ queryKey: ["api-keys"], queryFn: api.apiKeys });
  const createKey = useMutation({
    mutationFn: api.createApiKey,
    onSuccess: (key) => {
      setCreatedKey(key.api_key ?? null);
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    }
  });

  useEffect(() => {
    const socket = new WebSocket(websocketUrl(user.organization_id));
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as { name: string; source: string; at: string };
      setLiveEvents((items) => [`${payload.name} from ${payload.source} at ${payload.at}`, ...items].slice(0, 8));
    };
    return () => socket.close();
  }, [user.organization_id]);

  async function submitEvent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const response = await api.ingestEvent(apiKey, {
      name: String(data.get("name")),
      source: "manual",
      properties: { plan: data.get("plan"), region: data.get("region") }
    });
    setMessage(`Accepted ${response.accepted} event`);
    event.currentTarget.reset();
  }

  async function uploadCsv(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const file = data.get("file");
    if (!(file instanceof File)) return;
    const response = await api.uploadCsv(apiKey, file);
    setMessage(`Accepted ${response.accepted} CSV events`);
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
      <section className="space-y-4">
        <div className="rounded border border-slate-200 bg-white p-4">
          <h2 className="text-xl font-semibold text-ink">Event ingestion</h2>
          <p className="mt-1 text-sm text-slate-500">Use an API key to send events or upload CSV files.</p>
          <input
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            placeholder="Paste full API key"
            className="focus-ring mt-4 w-full rounded border px-3 py-3"
          />
          {message && <p className="mt-3 rounded bg-teal-50 px-3 py-2 text-sm text-mint">{message}</p>}
        </div>

        <form onSubmit={submitEvent} className="grid gap-3 rounded border border-slate-200 bg-white p-4 md:grid-cols-4">
          <input name="name" required placeholder="Event name" className="focus-ring rounded border px-3 py-2" />
          <input name="plan" placeholder="Plan" className="focus-ring rounded border px-3 py-2" />
          <input name="region" placeholder="Region" className="focus-ring rounded border px-3 py-2" />
          <button className="focus-ring flex items-center justify-center gap-2 rounded bg-mint px-3 py-2 text-white">
            <Send size={16} />
            Send
          </button>
        </form>

        <form onSubmit={uploadCsv} className="rounded border border-slate-200 bg-white p-4">
          <h3 className="font-semibold">CSV upload</h3>
          <div className="mt-3 flex flex-col gap-3 sm:flex-row">
            <input name="file" type="file" accept=".csv" className="focus-ring flex-1 rounded border px-3 py-2" />
            <button className="focus-ring flex items-center justify-center gap-2 rounded bg-ink px-4 py-2 text-white">
              <Upload size={16} />
              Upload
            </button>
          </div>
        </form>

        <section className="rounded border border-slate-200 bg-white p-4">
          <h3 className="font-semibold">Live event stream</h3>
          <div className="mt-3 min-h-28 space-y-2 text-sm text-slate-600">
            {liveEvents.length === 0 ? "Waiting for new events" : liveEvents.map((item) => <p key={item}>{item}</p>)}
          </div>
        </section>
      </section>

      <aside className="rounded border border-slate-200 bg-white p-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="font-semibold text-ink">API keys</h2>
          <button
            className="focus-ring flex items-center gap-2 rounded bg-ink px-3 py-2 text-sm text-white"
            onClick={() => createKey.mutate("Default ingestion key")}
          >
            <KeyRound size={16} />
            Generate
          </button>
        </div>
        {createdKey && (
          <p className="mt-4 break-all rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber">{createdKey}</p>
        )}
        <div className="mt-4 space-y-2">
          {keys.map((key) => (
            <div key={key.id} className="rounded border border-slate-200 p-3">
              <p className="font-medium">{key.name}</p>
              <p className="text-sm text-slate-500">{key.key_prefix} · {key.revoked ? "revoked" : "active"}</p>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}
