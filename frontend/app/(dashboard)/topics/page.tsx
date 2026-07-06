import { Suspense } from "react";

import { TopicLabTabs } from "@/components/TopicLabTabs";

export default function TopicsPage() {
  return (
    <div>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}>Topic Lab</h1>
      <p style={{ color: "var(--muted)", marginBottom: 24 }}>
        기능별 탭에서 주제를 고르고 → 시나리오 → 영상 → 채팅 수정까지 진행합니다.
      </p>

      <Suspense fallback={<p style={{ color: "var(--muted)" }}>탭 로딩 중…</p>}>
        <TopicLabTabs />
      </Suspense>
    </div>
  );
}
