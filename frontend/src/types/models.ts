export type Role = "Owner" | "Admin" | "Analyst" | "Viewer";
export type WidgetType = "line" | "bar" | "pie" | "kpi" | "table";

export interface UserContext {
  id: string;
  email: string;
  full_name: string;
  organization_id: string;
  organization_name: string;
  role: Role;
}

export interface AuthResponse {
  access_token: string;
  token_type: "bearer";
  user: UserContext;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  revoked: boolean;
  created_at: string;
  api_key?: string;
}

export interface Widget {
  id: string;
  dashboard_id: string;
  title: string;
  widget_type: WidgetType;
  metric_name: string;
  time_range: string;
  position: Record<string, unknown>;
  query_config: Record<string, unknown>;
}

export interface Dashboard {
  id: string;
  name: string;
  description: string | null;
  is_public: boolean;
  public_token: string | null;
  created_at: string;
  widgets: Widget[];
}

export interface ChartPoint {
  label: string;
  value: number;
}

export interface Member {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: Role;
}

export interface OrganizationCurrent {
  organization: { id: string; name: string };
  members: Member[];
}

export interface AlertRule {
  id: string;
  name: string;
  metric_name: string;
  operator: string;
  threshold: number;
  window_minutes: number;
  status: "Active" | "Triggered" | "Resolved" | "Muted";
  email_recipients: string[];
  webhook_url: string | null;
  muted_until: string | null;
}

export interface AlertHistory {
  id: string;
  alert_rule_id: string;
  triggered_value: number;
  status: "Active" | "Triggered" | "Resolved" | "Muted";
  message: string;
}

export interface ReportSchedule {
  id: string;
  dashboard_id: string;
  name: string;
  frequency: string;
  recipients: string[];
  snapshot_format: string;
  created_at: string;
}

export interface ReportRun {
  id: string;
  report_schedule_id: string;
  status: string;
  archive_url: string;
  created_at: string;
}

export interface Notification {
  id: string;
  alert_rule_id: string | null;
  channel: string;
  recipient: string | null;
  title: string;
  message: string;
  status: string;
  error: string | null;
  delivered_at: string | null;
  created_at: string;
}
