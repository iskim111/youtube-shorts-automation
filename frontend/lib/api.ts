import { getClientAuthToken, getServerAuthToken, isAuthEnabled } from "./auth";

const API_ROOT = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_BASE = `${API_ROOT}/api/v1`;

async function authHeaders(): Promise<Record<string, string>> {
  if (!isAuthEnabled()) return {};
  const token =
    typeof window === "undefined" ? await getServerAuthToken() : getClientAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const headers = { ...(await authHeaders()), ...(init?.headers as Record<string, string>) };
  const res = await fetch(url, { cache: "no-store", ...init, headers });  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error: ${res.status} ${text || url}`);
  }
  return res.json() as Promise<T>;
}

export type TopicCandidate = {
  id: string;
  category: string;
  keyword_cluster: string[];
  hook_line: string;
  scores: {
    view_potential: number;
    competition: number;
    production: number;
    copyright_safety: number;
    final: number;
  };
  copyright_risk: "low" | "medium" | "high";
  ai_label_required: boolean;
  status: string;
};

export type JobSummary = {
  id: string;
  channel_name: string;
  status: string;
  topic_score: number;
  hook_line: string;
};

export type JobDetail = {
  id: string;
  channel_name: string;
  status: string;
  operation_mode: string;
  topic_score: number;
  hook_line: string;
  stages: { stage: string; status: string; output_uri?: string | null }[];
  hold_reason: string | null;
  script: Record<string, unknown> | null;
  youtube_video_id: string | null;
  upload_dry_run: boolean | null;
  metadata_title: string | null;
  render_template: string;
  scheduled_publish_at: string | null;
  assets: { source_type: string; license_status: string; source_url: string | null }[];
};

export type CalendarSlot = {
  job_id: string;
  channel_name: string;
  hook_line: string;
  status: string;
  scheduled_publish_at: string | null;
  youtube_video_id: string | null;
  priority: number;
};

export type RightsQueueItem = {
  job_id: string | null;
  topic_id: string | null;
  hook_line: string;
  channel_name: string;
  status: string;
  hold_reason: string | null;
  copyright_risk: string | null;
  category: string | null;
};

export type PipelineRunResponse = {
  job_id: string;
  status: string;
  message: string;
};

export type PublishResponse = {
  job_id: string;
  status: string;
  youtube_video_id: string | null;
  dry_run: boolean;
  title: string;
  privacy_status: string;
};

export type Channel = {
  id: string;
  name: string;
  operation_mode: string;
  daily_upload_cap: number;
  category_allowlist: string[];
  is_active: boolean;
  youtube_channel_id: string | null;
  oauth_connected: boolean;
  youtube_channel_title: string | null;
};

export type OAuthStartResponse = {
  authorization_url: string;
  state: string;
};

export type OAuthStatus = {
  connected: boolean;
  youtube_channel_id: string | null;
  youtube_channel_title: string | null;
  scopes: string[];
  token_expires_at: string | null;
  last_refreshed_at: string | null;
};

export type SetupCheck = {
  id: string;
  label: string;
  ok: boolean;
  detail: string;
  path?: string | null;
  warning?: boolean;
};

export type SetupStatus = {
  ready_for_real_upload: boolean;
  checks: SetupCheck[];
  redirect_uri: string;
  quota?: HealthResponse["quota"];
};

export type HealthResponse = {
  status: string;
  version?: string;
  operation_mode: string;
  categories: string[];
  ffmpeg?: { available: boolean; path: string | null; version: string | null };
  youtube_oauth_configured?: boolean;
  pilot_dry_run_upload?: boolean;
  quota?: {
    youtube_insert_used: number;
    youtube_insert_limit: number;
    youtube_insert_remaining: number;
    usage_percent: number;
  };
};

export type AnalyticsOverview = {
  kpis: {
    total_jobs: number;
    published_jobs: number;
    hold_jobs: number;
    publish_success_rate: number;
    topic_to_publish_conversion: number;
  };
  quota: HealthResponse["quota"];
  category_performance: Record<
    string,
    { avg_views_24h: number; avg_retention: number; sample_count: number }
  >;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  role: string;
};

export type AuditLog = {
  id: string;
  actor_email: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  payload: Record<string, unknown> | null;
  created_at: string;
};

export const api = {
  login: (email: string, password: string) =>
    fetchJson<LoginResponse>(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    }),
  createChannel: (body: {
    name: string;
    operation_mode?: string;
    daily_upload_cap?: number;
    category_allowlist?: string[];
  }) =>
    fetchJson<Channel>(`${API_BASE}/channels`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  health: () => fetchJson<HealthResponse>(`${API_ROOT}/health`),
  setupStatus: () => fetchJson<SetupStatus>(`${API_BASE}/setup/status`),
  analyticsOverview: () => fetchJson<AnalyticsOverview>(`${API_BASE}/analytics/overview`),
  auditLogs: (entityType?: string) =>
    fetchJson<AuditLog[]>(
      `${API_BASE}/audit/logs${entityType ? `?entity_type=${entityType}` : ""}`
    ),
  topics: () => fetchJson<TopicCandidate[]>(`${API_BASE}/topics`),
  jobs: () => fetchJson<JobSummary[]>(`${API_BASE}/jobs`),
  job: (id: string) => fetchJson<JobDetail>(`${API_BASE}/jobs/${id}`),
  channels: () => fetchJson<Channel[]>(`${API_BASE}/channels`),
  channel: (id: string) => fetchJson<Channel>(`${API_BASE}/channels/${id}`),
  oauthStart: (channelId: string) =>
    fetchJson<OAuthStartResponse>(`${API_BASE}/channels/${channelId}/oauth/start`, {
      method: "POST",
    }),
  oauthStatus: (channelId: string) =>
    fetchJson<OAuthStatus>(`${API_BASE}/channels/${channelId}/oauth/status`),
  oauthDisconnect: (channelId: string) =>
    fetchJson(`${API_BASE}/channels/${channelId}/oauth`, { method: "DELETE" }),
  approveTopic: (topicId: string) =>
    fetchJson<{ topic_id: string; job_id: string; status: string }>(
      `${API_BASE}/topics/${topicId}/approve`,
      { method: "POST" }
    ),
  runPipeline: (jobId: string) =>
    fetchJson<PipelineRunResponse>(`${API_BASE}/jobs/${jobId}/run`, { method: "POST" }),
  publishJob: (jobId: string) =>
    fetchJson<PublishResponse>(`${API_BASE}/jobs/${jobId}/publish`, { method: "POST" }),
  retryJob: (jobId: string) =>
    fetchJson(`${API_BASE}/jobs/${jobId}/retry`, { method: "POST" }),
  scheduleJob: (jobId: string, scheduled_publish_at: string, render_template?: string) =>
    fetchJson(`${API_BASE}/jobs/${jobId}/schedule`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scheduled_publish_at, render_template }),
    }),
  calendar: () => fetchJson<CalendarSlot[]>(`${API_BASE}/uploads/calendar`),
  rightsQueue: () => fetchJson<RightsQueueItem[]>(`${API_BASE}/rights/queue`),
  reviewJob: (jobId: string, action: "approve" | "reject", note?: string) =>
    fetchJson(`${API_BASE}/rights/jobs/${jobId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, note }),
    }),
};
