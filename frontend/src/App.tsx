import { useEffect, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { api, getToken, setToken } from "./api/client";
import { AuthPanel } from "./components/AuthPanel";
import { Layout, type View } from "./components/Layout";
import { AlertsPage } from "./pages/AlertsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { IngestionPage } from "./pages/IngestionPage";
import { ReportsPage } from "./pages/ReportsPage";
import { TeamPage } from "./pages/TeamPage";
import type { UserContext } from "./types/models";

const queryClient = new QueryClient();

export function App() {
  const [user, setUser] = useState<UserContext | null>(null);
  const [view, setView] = useState<View>("dashboards");
  const [booting, setBooting] = useState(true);

  useEffect(() => {
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
      {!user ? (
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
        </Layout>
      )}
    </QueryClientProvider>
  );
}
