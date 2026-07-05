"use client";

import { useEffect, useState } from "react";

import { JobActions } from "@/components/JobActions";
import { JobReviewChat } from "@/components/JobReviewChat";
import { api, type Channel, type SeriesPreset } from "@/lib/api";

function JobWorkspace({ jobId }: { jobId: string }) {
  const [status, setStatus] = useState("TOPIC_APPROVED");
  const refreshJob = () => api.job(jobId).then((j) => setStatus(j.status)).catch(() => undefined);
  useEffect(() => {
    refreshJob();
  }, [jobId]);
  return (
    <div style={{ marginTop: 24, borderTop: "1px solid var(--border)", paddingTop: 24 }}>
      <h3 style={{ marginBottom: 12 }}>작업 · {jobId}</h3>
      <JobActions jobId={jobId} status={status} onComplete={refreshJob} />
      <JobReviewChat jobId={jobId} referenceMode />
    </div>
  );
}

export function SeriesEpisodePanel() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [channelId, setChannelId] = useState("");
  const [presets, setPresets] = useState<SeriesPreset[]>([]);
  const [preset, setPreset] = useState("grandma_youth_en");
  const [topicHint, setTopicHint] = useState("");
  const [creating, setCreating] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.channels().then(setChannels).catch(() => undefined);
    api.seriesPresets().then(setPresets).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (channels.length && !channelId) setChannelId(channels[0].id);
  }, [channels, channelId]);

  async function createEpisode() {
    if (!channelId) return;
    setCreating(true);
    setError(null);
    setActiveJobId(null);
    try {
      const res = await api.createSeriesEpisode(channelId, preset, topicHint);
      setActiveJobId(res.job_id);
    } catch (e) {
      setError(e instanceof Error ? e.message.replace(/^API error: \d+ /, "") : "에피소드 생성 실패");
    } finally {
      setCreating(false);
    }
  }

  return (
    <section style={{ marginBottom: 40 }}>
      <h2 style={{ fontSize: "1.1rem", marginBottom: 8 }}>시리즈 캐릭터 에피소드</h2>
      <p style={{ color: "var(--muted)", fontSize: "0.9rem", marginBottom: 12 }}>
        할머니+외국 청년 등 고정 주인공으로 한국어·영어 대화 Shorts를 만듭니다. Settings에서 Avatar/Voice ID를
        먼저 등록하세요.
      </p>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 12,
          marginBottom: 16,
          padding: 16,
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 12,
        }}
      >
        <select
          value={channelId}
          onChange={(e) => setChannelId(e.target.value)}
          style={{ padding: "8px 12px", borderRadius: 8, background: "var(--bg)", color: "inherit" }}
        >
          {channels.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <select
          value={preset}
          onChange={(e) => setPreset(e.target.value)}
          style={{ padding: "8px 12px", borderRadius: 8, background: "var(--bg)", color: "inherit" }}
        >
          {presets.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
        <input
          value={topicHint}
          onChange={(e) => setTopicHint(e.target.value)}
          placeholder="에피소드 주제 (선택) 예: 카페에서 인사하기"
          style={{
            flex: "1 1 200px",
            padding: "8px 12px",
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--bg)",
            color: "inherit",
          }}
        />
        <button
          type="button"
          onClick={createEpisode}
          disabled={creating}
          style={{
            padding: "8px 16px",
            borderRadius: 8,
            border: "none",
            background: "var(--accent)",
            color: "#fff",
            cursor: creating ? "wait" : "pointer",
          }}
        >
          {creating ? "생성 중…" : "에피소드 만들기"}
        </button>
      </div>
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      {activeJobId && <JobWorkspace jobId={activeJobId} />}
    </section>
  );
}
