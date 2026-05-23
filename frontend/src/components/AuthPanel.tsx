import { FormEvent, useState } from "react";
import { Activity } from "lucide-react";
import { api, setToken } from "../api/client";
import type { UserContext } from "../types/models";

interface Props {
  onAuthenticated: (user: UserContext) => void;
}

export function AuthPanel({ onAuthenticated }: Props) {
  const [mode, setMode] = useState<"login" | "signup">("signup");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    const data = new FormData(event.currentTarget);
    const email = String(data.get("email")).trim().toLowerCase();
    const password = String(data.get("password"));
    try {
      const response =
        mode === "signup"
          ? await api.signup({
              email,
              full_name: String(data.get("full_name")),
              password,
              organization_name: String(data.get("organization_name"))
            })
          : await api.login({
              email,
              password
            });
      setToken(response.access_token);
      onAuthenticated(response.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto grid min-h-screen max-w-6xl grid-cols-1 lg:grid-cols-[1fr_420px]">
        <section className="flex flex-col justify-between px-6 py-8 sm:px-10">
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded bg-mint text-white">
              <Activity size={22} />
            </span>
            <span className="text-xl font-semibold">Atlas Analytics</span>
          </div>
          <div className="max-w-2xl py-16">
            <h1 className="text-4xl font-semibold leading-tight sm:text-5xl">Real-time analytics for product teams.</h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-slate-300">
              Ingest events, manage tenant data, build dashboards, and keep your team aligned from one focused workspace.
            </p>
          </div>
          <div className="grid max-w-2xl grid-cols-3 gap-3 text-sm text-slate-300">
            <span>Multi-tenant</span>
            <span>Async ingestion</span>
            <span>Live dashboards</span>
          </div>
        </section>
        <section className="flex items-center bg-white px-6 py-10 text-ink sm:px-10">
          <form onSubmit={submit} className="w-full space-y-5">
            <div>
              <p className="text-sm font-medium text-mint">{mode === "signup" ? "Create workspace" : "Welcome back"}</p>
              <h2 className="mt-2 text-2xl font-semibold">{mode === "signup" ? "Start your analytics org" : "Sign in"}</h2>
            </div>
            {mode === "signup" && (
              <>
                <Field name="full_name" label="Full name" autoComplete="name" />
                <Field name="organization_name" label="Organization" />
              </>
            )}
            <Field name="email" label="Email" type="email" autoComplete="email" />
            <Field
              name="password"
              label="Password"
              type="password"
              autoComplete={mode === "signup" ? "new-password" : "current-password"}
            />
            {error && <p className="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose">{error}</p>}
            <button className="focus-ring w-full rounded bg-ink px-4 py-3 font-medium text-white" disabled={loading}>
              {loading ? "Working..." : mode === "signup" ? "Create account" : "Sign in"}
            </button>
            <button
              type="button"
              className="focus-ring w-full rounded border border-slate-300 px-4 py-3 text-sm font-medium"
              onClick={() => setMode(mode === "signup" ? "login" : "signup")}
            >
              {mode === "signup" ? "Use existing account" : "Create new account"}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}

function Field({
  name,
  label,
  type = "text",
  autoComplete
}: {
  name: string;
  label: string;
  type?: string;
  autoComplete?: string;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <input
        required
        name={name}
        type={type}
        autoComplete={autoComplete}
        className="focus-ring mt-2 w-full rounded border border-slate-300 px-3 py-3"
      />
    </label>
  );
}
