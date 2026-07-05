import { ReferenceShortsPanel } from "@/components/ReferenceShortsPanel";
import { SeriesEpisodePanel } from "@/components/SeriesEpisodePanel";
import { TopicLabPanel } from "@/components/TopicLabPanel";
import { TrendingShortsPanel } from "@/components/TrendingShortsPanel";

export default function TopicsPage() {
  return (
    <div>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}>Topic Lab</h1>
      <p style={{ color: "var(--muted)", marginBottom: 24 }}>
        TOP 100 · 시리즈 캐릭터 · 참조 URL → 시나리오 → 영상 → 채팅 수정
      </p>

      <TrendingShortsPanel />
      <SeriesEpisodePanel />
      <ReferenceShortsPanel />

      <details style={{ marginTop: 8 }}>
        <summary style={{ cursor: "pointer", fontWeight: 600, marginBottom: 16 }}>
          AI 주제 변형 생성 (선택)
        </summary>
        <TopicLabPanel />
      </details>
    </div>
  );
}
