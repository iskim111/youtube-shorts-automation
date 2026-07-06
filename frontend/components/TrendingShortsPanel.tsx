"use client";

import { useEffect, useState } from "react";

import { JobActions } from "@/components/JobActions";
import { JobReviewChat } from "@/components/JobReviewChat";
import { api, type Channel, type TrendingShort } from "@/lib/api";

function JobWorkspace({ jobId }: { jobId: string }) {
  const [status, setStatus] = useState("TOPIC_APPROVED");
  const refreshJob = () => api.job(jobId).then((job) => setStatus(job.status)).catch(() => undefined);

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

export function TrendingShortsPanel() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [channelId, setChannelId] = useState("");
  const [items, setItems] = useState<TrendingShort[]>([]);
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

  async function loadTrending() {
    setLoading(true);
    setError(null);

    try {
      const res = await api.trendingShorts(100);
      setItems(res.items);
      setLoadedOnce(true);

      if (res.items.length === 0) {
        setError("YouTube API 호출은 성공했지만 현재 조건에 맞는 Shorts 결과가 없습니다.");
      }
    } catch (e) {
      setError(
        e instanceof Error ? e.message.replace(/^API error: \d+ /, "") : "목록을 불러오지 못했습니다."
      );
    } finally {
      setLoading(false);
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
      <h2 style={{ fontSize: "1.1rem", marginBottom: 8 }}>인기 Shorts TOP 100</h2>
      <p style={{ color: "var(--muted)", fontSize: "0.9rem", marginBottom: 12 }}>
        한국 인기 Shorts에서 주제를 고르면 같은 주제로 새 시나리오와 영상 Job이 생성됩니다.
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
          onClick={loadTrending}
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
          {loading ? "불러오는 중..." : "TOP 100 불러오기"}
        </button>
      </div>
      {error && <p style={{ color: "var(--danger)", marginBottom: 12 }}>{error}</p>}
      {!loading && loadedOnce && items.length === 0 && !error && (
        <p style={{ color: "var(--muted)", marginBottom: 12 }}>
          조회는 완료됐지만 표시할 Shorts가 없습니다. API 키 제한사항이나 검색 조건을 확인해보세요.
        </p>
      )}
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
