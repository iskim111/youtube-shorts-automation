import Link from "next/link";

import { JobActions } from "@/components/JobActions";
import { JobSchedule } from "@/components/JobSchedule";
import { api } from "@/lib/api";

function stageIcon(status: string) {
  if (status === "success") return "✓";
  if (status === "failed") return "✗";
  if (status === "processing") return "…";
  return "○";
}

export default async function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let job = null;
  let error: string | null = null;

  try {
    job = await api.job(id);
  } catch (e) {
    error = e instanceof Error ? e.message : "API 연결 실패";
  }

  if (error) {
    return (
      <div>
        <h1>Job Detail</h1>
        <p style={{ color: "var(--danger)", marginTop: 16 }}>백엔드 미연결: {error}</p>
        <Link href="/overview" style={{ color: "var(--accent)", marginTop: 16, display: "inline-block" }}>
          ← Overview
        </Link>
      </div>
    );
  }

  if (!job) return null;

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <Link href="/overview" style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
          ← Overview
        </Link>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginTop: 8 }}>
          Job {job.id}
        </h1>
        <p style={{ color: "var(--muted)" }}>
          {job.channel_name} · {job.operation_mode} · 점수 {job.topic_score}
        </p>
      </div>

      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 12,
          padding: 24,
          marginBottom: 24,
        }}
      >
        <div style={{ fontSize: "0.85rem", color: "var(--muted)", marginBottom: 8 }}>훅</div>
        <div style={{ fontSize: "1.1rem", fontWeight: 600 }}>{job.hook_line}</div>
        <div style={{ marginTop: 16 }}>
          <span className="badge badge-warning">{job.status}</span>
          {job.hold_reason && (
            <span className="badge badge-danger" style={{ marginLeft: 8 }}>
              {job.hold_reason}
            </span>
          )}
          {job.youtube_video_id && (
            <span className="badge badge-success" style={{ marginLeft: 8 }}>
              {job.upload_dry_run ? "dry-run" : "YT"}: {job.youtube_video_id}
            </span>
          )}
        </div>
      </div>

      {job.script && (
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: 24,
            marginBottom: 24,
          }}
        >
          <h2 style={{ fontSize: "1rem", marginBottom: 12 }}>대본</h2>
          <pre
            style={{
              fontSize: "0.85rem",
              color: "var(--muted)",
              whiteSpace: "pre-wrap",
              lineHeight: 1.6,
            }}
          >
            {JSON.stringify(job.script, null, 2)}
          </pre>
        </div>
      )}

      <h2 style={{ fontSize: "1.1rem", marginBottom: 16 }}>파이프라인 진행</h2>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 8 }}>
        {job.stages.map((s) => (
          <div
            key={s.stage}
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "12px 16px",
              minWidth: 100,
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "1.2rem", marginBottom: 4 }}>{stageIcon(s.status)}</div>
            <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{s.stage}</div>
            <div style={{ fontSize: "0.75rem", marginTop: 4 }}>{s.status}</div>
          </div>
        ))}
      </div>

      {job.assets.length > 0 && (
        <div style={{ marginTop: 16, fontSize: "0.85rem", color: "var(--muted)" }}>
          애셋: {job.assets.map((a) => `${a.source_type}(${a.license_status})`).join(", ")}
        </div>
      )}

      <JobActions jobId={job.id} status={job.status} />
      <JobSchedule jobId={job.id} currentTemplate={job.render_template} />
      {job.scheduled_publish_at && (
        <p style={{ marginTop: 12, fontSize: "0.85rem", color: "var(--muted)" }}>
          예약: {new Date(job.scheduled_publish_at).toLocaleString("ko-KR")}
        </p>
      )}
    </div>
  );
}
