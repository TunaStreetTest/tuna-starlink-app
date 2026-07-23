export type HealthService = Record<string, unknown> & { ok?: boolean; error?: string };
export type Health = {
  ok: boolean;
  app: string;
  edge_text: string;
  art_path: string;
  services: Record<string, HealthService>;
};

export type Style = { id: string; label: string; description: string };

export type GalleryRun = {
  run_id: string;
  status: string;
  style_id?: string;
  style_label?: string;
  style_hashtag?: string;
  news_lane?: string;
  caption?: string;
  stream_slug?: string;
  events?: string;
  events_source?: string;
  created_at?: string;
  updated_at?: string;
  dry_run?: boolean;
  egress_bytes?: number;
  latency_ms?: number;
  has_image?: boolean;
  has_field?: boolean;
  raster_mode?: string;
  error?: string;
};

export type PipelineStatus = {
  current: Record<string, unknown> | null;
  recent: Array<Record<string, unknown>>;
  dry_run: boolean;
  schedule_enabled: boolean;
  schedule_cron: string | null;
  schedule_timezone?: string | null;
  schedule_interval_minutes?: number;
  auto_publish?: boolean;
  default_style: string;
  edge_text: string;
  x_account: string;
};

export type PublishStatus = {
  credentials_ready: boolean;
  handle: string;
  flow: { main: string; comment_1: string; comment_2: string };
};

export type PublishResult = {
  ok: boolean;
  already_posted?: boolean;
  run_id: string;
  x_post_id?: string;
  x_url?: string;
  handle?: string;
  caption?: string;
  replies?: Array<Record<string, unknown>>;
};

async function get<T>(path: string): Promise<T> {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path} → ${r.status} ${await r.text()}`);
  return r.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`${path} → ${r.status} ${await r.text()}`);
  return r.json();
}

export const api = {
  health: () => get<Health>("/api/health"),
  styles: () => get<{ styles: Style[] }>("/api/styles"),
  gallery: (limit = 50) => get<{ runs: GalleryRun[]; count: number }>(`/api/gallery?limit=${limit}`),
  run: (id: string) => get<Record<string, unknown>>(`/api/gallery/${id}`),
  pipeline: () => get<PipelineStatus>("/api/pipeline"),
  generate: (style?: string, force = false) =>
    post<{ started: boolean; message?: string; current?: unknown }>("/api/generate", {
      style: style || null,
      force,
      wait: false,
    }),
  imageUrl: (runId: string) => `/api/gallery/${runId}/image`,
  fieldUrl: (runId: string) => `/api/gallery/${runId}/field`,
  publishStatus: () => get<PublishStatus>("/api/publish/status"),
  publishPreview: (runId: string) => get<Record<string, unknown>>(`/api/publish/preview/${runId}`),
  publishX: (runId: string, withComments = false) =>
    post<PublishResult>("/api/publish/x", { run_id: runId, with_comments: withComments }),
};
