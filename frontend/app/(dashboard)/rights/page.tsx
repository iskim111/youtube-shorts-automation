import Link from "next/link";

import { RightsReview } from "@/components/RightsReview";
import { api, type RightsQueueItem } from "@/lib/api";

function riskBadge(risk: string | null) {
  if (risk === "low") return "badge-success";
  if (risk === "medium") return "badge-warning";
  return "badge-danger";
}

export default async function RightsPage() {
  let items: RightsQueueItem[] = [];
  let error: string | null = null;

  try {
    items = await api.rightsQueue();
  } catch (e) {
    error = e instanceof Error ? e.message : "API 연결 실패";
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}>Rights Center</h1>
      <p style={{ color: "var(--muted)", marginBottom: 32 }}>
        권리·정책 검수 대기 — 저작권 위험, QA/RIGHTS 보류 항목
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
              <th>Job / Topic</th>
              <th>훅</th>
              <th>카테고리</th>
              <th>저작권</th>
              <th>상태</th>
              <th>사유</th>
              <th>액션</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, i) => (
              <tr key={`${item.job_id}-${item.topic_id}-${i}`}>
                <td>
                  {item.job_id ? (
                    <Link href={`/jobs/${item.job_id}`} style={{ color: "var(--accent)" }}>
                      {item.job_id}
                    </Link>
                  ) : (
                    item.topic_id
                  )}
                </td>
                <td>{item.hook_line}</td>
                <td>{item.category ?? "-"}</td>
                <td>
                  {item.copyright_risk && (
                    <span className={`badge ${riskBadge(item.copyright_risk)}`}>
                      {item.copyright_risk}
                    </span>
                  )}
                </td>
                <td>
                  <span className="badge badge-warning">{item.status}</span>
                </td>
                <td style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                  {item.hold_reason ?? "-"}
                </td>
                <td>
                  <RightsReview item={item} />
                </td>
              </tr>
            ))}
            {items.length === 0 && !error && (
              <tr>
                <td colSpan={7} style={{ color: "var(--muted)" }}>
                  검수 대기 항목 없음
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
