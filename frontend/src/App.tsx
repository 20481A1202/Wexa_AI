"use client";

import { useEffect, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { api, getToken, setToken } from "./api/client";
import { AuthPanel } from "./components/AuthPanel";
import { Layout, type View } from "./components/Layout";
import { AlertsPage } from "./features/AlertsPage";
import { DashboardPage } from "./features/DashboardPage";
import { IngestionPage } from "./features/IngestionPage";
import { PublicDashboardPage } from "./features/PublicDashboardPage";
import { ReportsPage } from "./features/ReportsPage";
import { TeamPage } from "./features/TeamPage";
import type { UserContext } from "./types/models";

const queryClient = new QueryClient();

export function App() {
  const [user, setUser] = useState<UserContext | null>(null);
  const [view, setView] = useState<View>("dashboards");
  const [booting, setBooting] = useState(true);
  const [publicDashboardToken, setPublicDashboardToken] = useState<string | null>(null);
  const [inviteToken, setInviteToken] = useState<string | null>(null);
  const [inviteStatus, setInviteStatus] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setPublicDashboardToken(params.get("dashboard"));
    setInviteToken(params.get("invite_token"));
    if (!getToken()) {
      setBooting(false);
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setBooting(false));
  }, []);

  if (booting) return <div className="grid min-h-screen place-items-center bg-slate-100 text-slate-600">Loading workspace</div>;

  return (
    <QueryClientProvider client={queryClient}>
      {publicDashboardToken ? (
        <PublicDashboardPage token={publicDashboardToken} />
      ) : !user ? (
        <AuthPanel onAuthenticated={setUser} />
      ) : (
        <Layout
          user={user}
          view={view}
          onView={setView}
          onLogout={() => {
            api.logout().finally(() => setUser(null));
          }}
        >
          {view === "dashboards" && <DashboardPage />}
          {view === "ingestion" && <IngestionPage user={user} />}
          {view === "team" && <TeamPage />}
          {view === "alerts" && <AlertsPage />}
          {view === "reports" && <ReportsPage />}
          {inviteToken && (
            <div className="fixed bottom-4 right-4 max-w-md rounded border border-slate-200 bg-white p-4 text-sm shadow">
              <p className="font-semibold text-ink">Pending invite</p>
              <p className="mt-1 text-slate-600">Accept this invite for {user.email}.</p>
              {inviteStatus && <p className="mt-2 text-mint">{inviteStatus}</p>}
              <button
                className="focus-ring mt-3 rounded bg-mint px-3 py-2 text-white"
                onClick={() =>
                  api
                    .acceptInvite(inviteToken)
                    .then(() => {
                      setInviteStatus("Invite accepted. Refreshing workspace.");
                      setTimeout(() => window.location.assign(window.location.pathname), 900);
                    })
                    .catch((error) => setInviteStatus(error instanceof Error ? error.message : "Invite could not be accepted"))
                }
              >
                Accept invite
              </button>
            </div>
          )}
        </Layout>
      )}
    </QueryClientProvider>
  );
}
