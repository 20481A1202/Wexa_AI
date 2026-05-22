import type {
  AlertRule,
  AlertHistory,
  ApiKey,
  AuthResponse,
  ChartPoint,
  Dashboard,
  Notification,
  OrganizationCurrent,
  ReportRun,
  ReportSchedule,
  Role,
  Widget,
  WidgetType
} from "../types/models";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "atlas_access_token";

export function websocketUrl(organizationId: string) {
  const token = encodeURIComponent(getToken() ?? "");
  return `${API_BASE.replace(/^http/, "ws")}/ws/events/${organizationId}?token=${token}`;
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: "include"
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(payload.detail ?? "Request failed");
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  signup(payload: { email: string; full_name: string; password: string; organization_name: string }) {
    return request<AuthResponse>("/auth/signup", { method: "POST", body: JSON.stringify(payload) });
  },
  login(payload: { email: string; password: string }) {
    return request<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify(payload) });
  },
  me() {
    return request<AuthResponse["user"]>("/auth/me");
  },
  logout() {
    setToken(null);
    return request<void>("/auth/logout", { method: "POST" });
  },
  organization() {
    return request<OrganizationCurrent>("/organizations/current");
  },
  invite(payload: { email: string; role: Role }) {
    return request<{ token: string }>("/organizations/invites", { method: "POST", body: JSON.stringify(payload) });
  },
  updateMember(memberId: string, role: Role) {
    return request(`/organizations/members/${memberId}`, { method: "PATCH", body: JSON.stringify({ role }) });
  },
  apiKeys() {
    return request<ApiKey[]>("/api-keys");
  },
  createApiKey(name: string) {
    return request<ApiKey>("/api-keys", { method: "POST", body: JSON.stringify({ name }) });
  },
  revokeApiKey(id: string) {
    return request<void>(`/api-keys/${id}`, { method: "DELETE" });
  },
  dashboards() {
    return request<Dashboard[]>("/dashboards");
  },
  createDashboard(payload: { name: string; description?: string; is_public?: boolean }) {
    return request<Dashboard>("/dashboards", { method: "POST", body: JSON.stringify(payload) });
  },
  updateDashboard(id: string, payload: Partial<Pick<Dashboard, "name" | "description" | "is_public">>) {
    return request<Dashboard>(`/dashboards/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
  },
  createWidget(
    dashboardId: string,
    payload: { title: string; widget_type: WidgetType; metric_name: string; time_range: string }
  ) {
    return request<Widget>(`/dashboards/${dashboardId}/widgets`, { method: "POST", body: JSON.stringify(payload) });
  },
  widgetData(dashboardId: string, widgetId: string) {
    return request<{ widget_id: string; points: ChartPoint[] }>(`/dashboards/${dashboardId}/widgets/${widgetId}/data`);
  },
  ingestEvent(apiKey: string, payload: { name: string; source: string; properties: Record<string, unknown> }) {
    return request<{ accepted: number }>("/ingest/events", {
      method: "POST",
      headers: { "X-API-Key": apiKey },
      body: JSON.stringify(payload)
    });
  },
  uploadCsv(apiKey: string, file: File) {
    const data = new FormData();
    data.append("file", file);
    return request<{ accepted: number }>("/ingest/csv", {
      method: "POST",
      headers: { "X-API-Key": apiKey },
      body: data
    });
  },
  alerts() {
    return request<AlertRule[]>("/alerts");
  },
  alertHistory() {
    return request<AlertHistory[]>("/alerts/history");
  },
  evaluateAlerts() {
    return request<{ triggered: number }>("/alerts/evaluate", { method: "POST" });
  },
  createAlert(payload: {
    name: string;
    metric_name: string;
    operator: string;
    threshold: number;
    window_minutes: number;
    email_recipients: string[];
    webhook_url?: string | null;
  }) {
    return request<AlertRule>("/alerts", { method: "POST", body: JSON.stringify(payload) });
  },
  muteAlert(alertId: string, minutes: number) {
    return request<AlertRule>(`/alerts/${alertId}/mute`, { method: "POST", body: JSON.stringify({ minutes }) });
  },
  notifications() {
    return request<Notification[]>("/notifications");
  },
  reports() {
    return request<ReportSchedule[]>("/reports");
  },
  createReport(payload: {
    dashboard_id: string;
    name: string;
    frequency: string;
    recipients: string[];
    snapshot_format: string;
  }) {
    return request<ReportSchedule>("/reports", { method: "POST", body: JSON.stringify(payload) });
  },
  runReport(reportId: string) {
    return request<ReportRun>(`/reports/${reportId}/run`, { method: "POST" });
  }
};
