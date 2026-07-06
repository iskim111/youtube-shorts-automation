"use client";

import { useEffect, useState } from "react";

import { JobActions } from "@/components/JobActions";
import { JobReviewChat } from "@/components/JobReviewChat";
import {
  api,
  type Channel,
  type TrendingKeyword,
  type TrendingShort,
} from "@/lib/api";

function JobWorkspace({ jobId }: { jobId: string }) {
  const [status, setStatus] = useState("TOPIC_APPROVED");
  const refreshJob = () => api.job(jobId).then((j) => setStatus(j.status)).catch(() => undefined);

  useEffect(() => {
    refreshJob();
  }, [jobId]);

  return (
    <div style={{ marginTop: 24, borderTop: "1px solid var(--border)", paddingTop: 24 }}>
      <h3 style={{ marginBottom: 12 }}>작업 중인 Job {jobId}</h3>
      <JobActions jobId={jobId} status={status} onComplete={refreshJob} />
      <JobReviewChat jobId={jobId} referenceMode />
    </div>
  );
}

function KeywordList({
  title,
  items,
  selected,
  creating,
  onSelect,
}: {
  title: string;
  items: TrendingKeyword[];
  selected: string | null;
  creating: string | null;
  onSelect: (kw: TrendingKeyword) => void;
}) {
  if (items.length === 0) {
    return (
      <div>
        <h3 style={{ fontSize: "0.95rem", marginBottom: 8 }}>{title}</h3>
        <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>데이터 없음</p>
      </div>
    );
  }

  return (
    <div>
      <h3 style={{ fontSize: "0.95rem", marginBottom: 8 }}>{title}</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 360, overflowY: "auto" }}>
        {items.map((kw) => (
          <button
            key={`${kw.source}-${kw.rank}-${kw.keyword}`}
            type="button"
            onClick={() => onSelect(kw)}
            disabled={creating === kw.keyword}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "8px 12px",
              borderRadius: 8,
              border: selected === kw.keyword ? "1px solid var(--accent)" : "1px solid var(--border)",
              background: selected === kw.keyword ? "rgba(255,69,58,0.08)" : "var(--surface)",
              color: "inherit",
              cursor: "pointer",
              textAlign: "left",
            }}
          >
            <span style={{ fontWeight: 700, minWidth: 24, color: "var(--accent)" }}>{kw.rank}</span>
            <span style={{ flex: 1, fontSize: "0.9rem" }}>{kw.keyword}</span>
            {kw.traffic && (
              <span style={{ fontSize: "0.75rem", color: "var(--muted)" }}>{kw.traffic}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

export function TrendingShortsPanel() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [channelId, setChannelId] = useState("");
  const [googleKeywords, setGoogleKeywords] = useState<TrendingKeyword[]>([]);
  const [naverKeywords, setNaverKeywords] = useState<TrendingKeyword[]>([]);
  const [items, setItems] = useState<TrendingShort[]>([]);
  const [selectedKeyword, setSelectedKeyword] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadedOnce, setLoadedOnce] = useState(false);
  const [creating, setCreating] = useState<string | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.channels().then(setChannels).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (channels.length > 0 && !channelId) {
      setChannelId(channels[0].id);
    }
  }, [channels, channelId]);

  async function loadAll() {
    setLoading(true);
    setError(null);

    try {
      const [kwRes, shortsRes] = await Promise.all([
        api.trendingKeywords(100),
        api.trendingShorts(100),
      ]);
      setGoogleKeywords(kwRes.google);
      setNaverKeywords(kwRes.naver);
      setItems(shortsRes.items);
      setSelectedKeyword(null);
      setLoadedOnce(true);

      if (shortsRes.items.length === 0) {
        setError("인기 검색어는 불러왔지만 관련 Shorts가 없습니다. 키워드를 클릭해 다시 검색해보세요.");
      }
    } catch (e) {
      setError(
        e instanceof Error ? e.message.replace(/^API error: \d+ /, "") : "목록을 불러오지 못했습니다."
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadShortsForKeyword(kw: TrendingKeyword) {
    setSelectedKeyword(kw.keyword);
    setLoading(true);
    setError(null);

    try {
      const res = await api.trendingShorts(50, kw.keyword);
      setItems(res.items);
      if (res.items.length === 0) {
        setError(`「${kw.keyword}」 관련 Shorts를 찾지 못했습니다.`);
      }
    } catch (e) {
      setError(
        e instanceof Error ? e.message.replace(/^API error: \d+ /, "") : "Shorts 검색 실패"
      );
    } finally {
      setLoading(false);
    }
  }

  async function createFromKeyword(kw: TrendingKeyword) {
    if (!channelId) return;
    setCreating(kw.keyword);
    setError(null);
    setActiveJobId(null);

    try {
      const res = await api.createFromKeyword(kw.keyword, channelId, kw.source);
      setActiveJobId(res.job_id);
    } catch (e) {
      setError(
        e instanceof Error ? e.message.replace(/^API error: \d+ /, "") : "Job 생성 실패"
      );
    } finally {
      setCreating(null);
    }
  }

  async function selectItem(videoId: string) {
    if (!channelId) return;

    setCreating(videoId);
    setError(null);
    setActiveJobId(null);

    try {
      const res = await api.createFromTrending(videoId, channelId);
      setActiveJobId(res.job_id);
    } catch (e) {
      setError(
        e instanceof Error ? e.message.replace(/^API error: \d+ /, "") : "생성에 실패했습니다."
      );
    } finally {
      setCreating(null);
    }
  }

  return (
    <section style={{ marginBottom: 40 }}>
      <h2 style={{ fontSize: "1.1rem", marginBottom: 8 }}>오늘의 인기 검색어 TOP 100 · Shorts</h2>
      <p style={{ color: "var(--muted)", fontSize: "0.9rem", marginBottom: 12 }}>
        Google·네이버 시드 검색어 + 자동완성 확장 TOP 100 → 키워드별 최근 7일 인기 Shorts 검색
      </p>
      <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        <select
          value={channelId}
          onChange={(e) => setChannelId(e.target.value)}
          style={{ padding: "8px 12px", borderRadius: 8, background: "var(--bg)", color: "inherit" }}
        >
          {channels.map((channel) => (
            <option key={channel.id} value={channel.id}>
              {channel.name}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={loadAll}
          disabled={loading}
          style={{
            padding: "8px 16px",
            borderRadius: 8,
            border: "none",
            background: "var(--accent)",
            color: "#fff",
            cursor: "pointer",
          }}
        >
          {loading ? "불러오는 중..." : "인기 검색어 + Shorts 불러오기"}
        </button>
        {selectedKeyword && (
          <button
            type="button"
            onClick={loadAll}
            disabled={loading}
            style={{
              padding: "8px 16px",
              borderRadius: 8,
              border: "1px solid var(--border)",
              background: "var(--surface)",
              color: "inherit",
              cursor: "pointer",
            }}
          >
            전체 Shorts로 돌아가기
          </button>
        )}
      </div>

      {error && <p style={{ color: "var(--danger)", marginBottom: 12 }}>{error}</p>}

      {loadedOnce && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 16,
            marginBottom: 20,
          }}
        >
          <KeywordList
            title="Google TOP 100"
            items={googleKeywords}
            selected={selectedKeyword}
            creating={creating}
            onSelect={(kw) => {
              loadShortsForKeyword(kw);
            }}
          />
          <KeywordList
            title="네이버 TOP 100"
            items={naverKeywords}
            selected={selectedKeyword}
            creating={creating}
            onSelect={(kw) => {
              loadShortsForKeyword(kw);
            }}
          />
        </div>
      )}

      {loadedOnce && (googleKeywords.length > 0 || naverKeywords.length > 0) && (
        <p style={{ fontSize: "0.8rem", color: "var(--muted)", marginBottom: 12 }}>
          키워드 클릭 → 관련 Shorts 필터 · 키워드 옆에서 Job 생성하려면 아래 버튼 사용
        </p>
      )}

      {selectedKeyword && (
        <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
          <span style={{ fontSize: "0.9rem" }}>
            선택: <strong>{selectedKeyword}</strong>
          </span>
          <button
            type="button"
            disabled={!!creating || !channelId}
            onClick={() =>
              createFromKeyword({
                rank: 0,
                keyword: selectedKeyword,
                source: "combined",
              })
            }
            style={{
              padding: "6px 12px",
              borderRadius: 8,
              border: "none",
              background: "var(--accent)",
              color: "#fff",
              cursor: "pointer",
              fontSize: "0.85rem",
            }}
          >
            이 키워드로 Job 생성
          </button>
        </div>
      )}

      <h3 style={{ fontSize: "1rem", marginBottom: 12 }}>
        {selectedKeyword ? `「${selectedKeyword}」 관련 Shorts` : "인기 검색어 기반 Shorts"}
      </h3>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
          gap: 12,
          maxHeight: 420,
          overflowY: "auto",
        }}
      >
        {items.map((item) => (
          <button
            key={item.video_id}
            type="button"
            onClick={() => selectItem(item.video_id)}
            disabled={creating === item.video_id}
            style={{
              textAlign: "left",
              padding: 12,
              borderRadius: 12,
              border: "1px solid var(--border)",
              background: "var(--surface)",
              color: "inherit",
              cursor: "pointer",
            }}
          >
            {item.thumbnail_url && (
              <img
                src={item.thumbnail_url}
                alt=""
                style={{
                  width: "100%",
                  borderRadius: 8,
                  marginBottom: 8,
                  aspectRatio: "16/9",
                  objectFit: "cover",
                }}
              />
            )}
            <div style={{ fontSize: "0.85rem", fontWeight: 600, lineHeight: 1.4 }}>{item.title}</div>
            <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginTop: 4 }}>
              {item.channel_title} · 조회수 {item.view_count.toLocaleString()}
            </div>
            {item.matched_keyword && (
              <div style={{ fontSize: "0.75rem", color: "var(--accent)", marginTop: 4 }}>
                키워드: {item.matched_keyword}
                {item.keyword_source ? ` (${item.keyword_source})` : ""}
              </div>
            )}
            {creating === item.video_id && (
              <div style={{ fontSize: "0.8rem", color: "var(--accent)", marginTop: 6 }}>
                시나리오 생성 중...
              </div>
            )}
          </button>
        ))}
      </div>

      {activeJobId && <JobWorkspace jobId={activeJobId} />}
    </section>
  );
}
