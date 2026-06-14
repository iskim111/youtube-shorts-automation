import Link from "next/link";

import { TopicActions } from "@/components/TopicActions";
import { api, type TopicCandidate } from "@/lib/api";

function riskBadge(risk: string) {
  if (risk === "low") return "badge-success";
  if (risk === "medium") return "badge-warning";
  return "badge-danger";
}

function statusBadge(status: string) {
  if (status === "recommended") return "badge-success";
  if (status === "review_required") return "badge-warning";
  return "badge-muted";
}

export default async function TopicsPage() {
  let topics: TopicCandidate[] = [];
  let error: string | null = null;

  try {
    topics = await api.topics();
  } catch (e) {
    error = e instanceof Error ? e.message : "API 연결 실패";
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}>Topic Lab</h1>
      <p style={{ color: "var(--muted)", marginBottom: 32 }}>
        주제 후보 점수 · 승인/폐기 (Semi-auto: 승인 후 Job 생성)
      </p>

      {error && (
        <div style={{ color: "var(--danger)", marginBottom: 24 }}>백엔드 미연결: {error}</div>
      )}

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
              <th>ID</th>
              <th>소재군</th>
              <th>키워드</th>
              <th>한 줄 훅</th>
              <th>조회 잠재력</th>
              <th>저작권</th>
              <th>최종점수</th>
              <th>상태</th>
              <th>액션</th>
            </tr>
          </thead>
          <tbody>
            {topics.map((t) => (
              <tr key={t.id}>
                <td>{t.id}</td>
                <td>{t.category}</td>
                <td>{t.keyword_cluster.join(" / ")}</td>
                <td>{t.hook_line}</td>
                <td>{t.scores.view_potential}</td>
                <td>
                  <span className={`badge ${riskBadge(t.copyright_risk)}`}>{t.copyright_risk}</span>
                </td>
                <td style={{ fontWeight: 700 }}>{t.scores.final}</td>
                <td>
                  <span className={`badge ${statusBadge(t.status)}`}>{t.status}</span>
                </td>
                <td>
                  <TopicActions topicId={t.id} status={t.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
