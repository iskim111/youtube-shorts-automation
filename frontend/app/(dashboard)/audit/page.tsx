import { api, type AuditLog } from "@/lib/api";

function formatDt(iso: string) {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("ko-KR");
}

export default async function AuditPage() {
  let logs: AuditLog[] = [];
  let error: string | null = null;

  try {
    logs = await api.auditLogs();
  } catch (e) {
    error = e instanceof Error ? e.message : "API 연결 실패";
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}>Audit Logs</h1>
      <p style={{ color: "var(--muted)", marginBottom: 32 }}>
        운영자 활동 · 업로드 · 파이프라인 · 자동 게시 기록
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
              <th>시각</th>
              <th>액션</th>
              <th>엔티티</th>
              <th>ID</th>
              <th>상세</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                  {formatDt(log.created_at)}
                </td>
                <td>
                  <span className="badge badge-muted">{log.action}</span>
                </td>
                <td>{log.entity_type}</td>
                <td>{log.entity_id}</td>
                <td style={{ fontSize: "0.8rem", color: "var(--muted)", maxWidth: 280 }}>
                  {log.payload ? JSON.stringify(log.payload) : "-"}
                </td>
              </tr>
            ))}
            {logs.length === 0 && !error && (
              <tr>
                <td colSpan={5} style={{ color: "var(--muted)" }}>
                  감사 로그 없음
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
