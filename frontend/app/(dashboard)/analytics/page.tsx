import { StatCard } from "@/components/StatCard";
import { api, type AnalyticsOverview } from "@/lib/api";

export default async function AnalyticsPage() {
  let data: AnalyticsOverview | null = null;
  let error: string | null = null;

  try {
    data = await api.analyticsOverview();
  } catch (e) {
    error = e instanceof Error ? e.message : "API 연결 실패";
  }

  const kpis = data?.kpis;
  const quota = data?.quota;
  const perf = data?.category_performance ?? {};

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}>Analytics</h1>
      <p style={{ color: "var(--muted)", marginBottom: 32 }}>
        KPI · 쿼터 · 카테고리별 성과 (Topic Engine 피드백 루프)
      </p>

      {error && <div style={{ color: "var(--danger)", marginBottom: 24 }}>{error}</div>}

      {kpis && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: 16,
            marginBottom: 32,
          }}
        >
          <StatCard label="총 작업" value={kpis.total_jobs} />
          <StatCard label="게시 완료" value={kpis.published_jobs} />
          <StatCard label="보류" value={kpis.hold_jobs} />
          <StatCard label="게시 성공률" value={`${kpis.publish_success_rate}%`} />
          <StatCard label="후보→게시 전환" value={`${kpis.topic_to_publish_conversion}%`} />
          {quota && (
            <StatCard
              label="YouTube 쿼터"
              value={`${quota.youtube_insert_used}/${quota.youtube_insert_limit}`}
              sub={`${quota.usage_percent}% 사용`}
            />
          )}
        </div>
      )}

      <h2 style={{ fontSize: "1.1rem", marginBottom: 16 }}>카테고리별 성과</h2>
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
              <th>카테고리</th>
              <th>24h 평균 조회</th>
              <th>Retention</th>
              <th>샘플 수</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(perf).map(([cat, v]) => (
              <tr key={cat}>
                <td>{cat}</td>
                <td>{Math.round(v.avg_views_24h)}</td>
                <td>{(v.avg_retention * 100).toFixed(1)}%</td>
                <td>{v.sample_count}</td>
              </tr>
            ))}
            {Object.keys(perf).length === 0 && (
              <tr>
                <td colSpan={4} style={{ color: "var(--muted)" }}>
                  게시 후 성과 데이터가 쌓이면 표시됩니다.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
