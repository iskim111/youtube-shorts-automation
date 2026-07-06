"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

import { ReferenceShortsPanel } from "@/components/ReferenceShortsPanel";
import { SeriesEpisodePanel } from "@/components/SeriesEpisodePanel";
import { TopicLabPanel } from "@/components/TopicLabPanel";
import { TrendingShortsPanel } from "@/components/TrendingShortsPanel";

const TABS = [
  {
    id: "trending",
    label: "인기 검색어 TOP 100",
    description: "Google·네이버 인기 검색어로 Shorts 주제 찾기",
  },
  {
    id: "series",
    label: "시리즈 캐릭터",
    description: "고정 캐릭터 대화형 에피소드 생성",
  },
  {
    id: "reference",
    label: "참조 Shorts",
    description: "URL 분석 후 비슷한 구조로 새 영상 만들기",
  },
  {
    id: "ai",
    label: "AI 주제 생성",
    description: "트렌드·AI 혼합 주제 카드 생성 (선택)",
  },
] as const;

type TabId = (typeof TABS)[number]["id"];

function isTabId(value: string | null): value is TabId {
  return TABS.some((tab) => tab.id === value);
}

export function TopicLabTabs() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const raw = searchParams.get("tab");
  const active: TabId = isTabId(raw) ? raw : "trending";
  const current = TABS.find((tab) => tab.id === active) ?? TABS[0];

  const setTab = useCallback(
    (id: TabId) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set("tab", id);
      router.replace(`/topics?${params.toString()}`, { scroll: false });
    },
    [router, searchParams]
  );

  return (
    <div>
      <div
        role="tablist"
        aria-label="Topic Lab 기능"
        style={{
          display: "flex",
          gap: 8,
          flexWrap: "wrap",
          marginBottom: 20,
          borderBottom: "1px solid var(--border)",
          paddingBottom: 4,
        }}
      >
        {TABS.map((tab) => {
          const selected = tab.id === active;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={selected}
              onClick={() => setTab(tab.id)}
              style={{
                padding: "10px 16px",
                borderRadius: "8px 8px 0 0",
                border: selected ? "1px solid var(--border)" : "1px solid transparent",
                borderBottom: selected ? "1px solid var(--surface)" : "1px solid transparent",
                marginBottom: -1,
                background: selected ? "var(--surface)" : "transparent",
                color: selected ? "inherit" : "var(--muted)",
                fontWeight: selected ? 600 : 500,
                fontSize: "0.9rem",
                cursor: "pointer",
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      <p style={{ color: "var(--muted)", fontSize: "0.9rem", marginBottom: 20 }}>{current.description}</p>

      <div role="tabpanel">
        {active === "trending" && <TrendingShortsPanel />}
        {active === "series" && <SeriesEpisodePanel />}
        {active === "reference" && <ReferenceShortsPanel />}
        {active === "ai" && <TopicLabPanel />}
      </div>
    </div>
  );
}
