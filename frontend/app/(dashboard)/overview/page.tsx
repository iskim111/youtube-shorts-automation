import Link from "next/link";

import { StatCard } from "@/components/StatCard";
import { api, type Channel, type HealthResponse, type JobSummary } from "@/lib/api";

export default async function OverviewPage() {
  let health: HealthResponse | null = null;
  let jobs: JobSummary[] = [];
  let channels: Channel[] = [];
  let error: string | null = null;

  try {
    [health, jobs, channels] = await Promise.all([api.health(), api.jobs(), api.channels()]);
  } catch (e) {
    error = e instanceof Error ? e.message : "API 연결 실패";
  }

  const channel = channels[0];

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}>Overview</h1>
      <p style={{ color: "var(--muted)", marginBottom: 32 }}>
        채널별 작업 현황 · Semi-auto 운영 총괄
      </p>

      {error && (
        <div
          style={{
            background: "rgba(255,69,58,0.1)",
            border: "1px solid var(--danger)",
            borderRadius: 8,
            padding: 16,
            marginBottom: 24,
            color: "var(--danger)",
          }}
        >
          백엔드 미연결: {error}
          <div style={{ fontSize: "0.85rem", marginTop: 8, color: "var(--muted)" }}>
            `docker compose up` 후 `uvicorn app.main:app --reload` 실행 필요
          </div>
        </div>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 16,
          marginBottom: 32,
        }}
      >
        <StatCard label="운영 모드" value={health?.operation_mode ?? "semi_auto"} />
        <StatCard label="오늘 작업" value={jobs.length} sub="스텁 데이터" />
        <StatCard label="일일 업로드 캡" value={channel?.daily_upload_cap ?? 5} />
        <StatCard label="활성 카테고리" value={health?.categories.length ?? 4} />
        {health?.quota && (
          <StatCard
            label="YouTube 쿼터"
            value={`${health.quota.youtube_insert_used}/${health.quota.youtube_insert_limit}`}
            sub={`${health.quota.usage_percent}%`}
          />
        )}
      </div>

      <section>
        <h2 style={{ fontSize: "1.1rem", marginBottom: 16 }}>최근 작업</h2>
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            overflow: "hidden",
          }}
        >
          <table>
            <thead>
              <tr>
                <th>Job ID</th>
                <th>채널</th>
                <th>훅</th>
                <th>점수</th>
                <th>상태</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td>
                    <Link href={`/jobs/${job.id}`} style={{ color: "var(--accent)" }}>
                      {job.id}
                    </Link>
                  </td>
                  <td>{job.channel_name}</td>
                  <td>{job.hook_line}</td>
                  <td>{job.topic_score}</td>
                  <td>
                    <span className="badge badge-warning">{job.status}</span>
                  </td>
                </tr>
              ))}
              {jobs.length === 0 && !error && (
                <tr>
                  <td colSpan={5} style={{ color: "var(--muted)" }}>
                    작업 없음
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
