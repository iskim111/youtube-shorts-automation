import Link from "next/link";

import { api, type CalendarSlot } from "@/lib/api";

function formatDt(iso: string | null) {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default async function CalendarPage() {
  let slots: CalendarSlot[] = [];
  let error: string | null = null;

  try {
    slots = await api.calendar();
  } catch (e) {
    error = e instanceof Error ? e.message : "API 연결 실패";
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}>Upload Calendar</h1>
      <p style={{ color: "var(--muted)", marginBottom: 32 }}>
        예약 게시 슬롯 · Celery Beat가 QA_APPROVED + 예약 시각 도래 시 자동 업로드
      </p>

      {error && <div style={{ color: "var(--danger)", marginBottom: 24 }}>{error}</div>}

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
              <th>예약 시각</th>
              <th>Job</th>
              <th>채널</th>
              <th>훅</th>
              <th>상태</th>
              <th>Video ID</th>
            </tr>
          </thead>
          <tbody>
            {slots.map((s) => (
              <tr key={s.job_id}>
                <td>{formatDt(s.scheduled_publish_at)}</td>
                <td>
                  <Link href={`/jobs/${s.job_id}`} style={{ color: "var(--accent)" }}>
                    {s.job_id}
                  </Link>
                </td>
                <td>{s.channel_name}</td>
                <td>{s.hook_line}</td>
                <td>
                  <span className="badge badge-warning">{s.status}</span>
                </td>
                <td>{s.youtube_video_id ?? "-"}</td>
              </tr>
            ))}
            {slots.length === 0 && !error && (
              <tr>
                <td colSpan={6} style={{ color: "var(--muted)" }}>
                  예약된 업로드 없음 — Job Detail에서 예약 설정
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
