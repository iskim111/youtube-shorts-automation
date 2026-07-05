"use client";

import { useEffect, useState } from "react";

import { JobActions } from "@/components/JobActions";
import { JobReviewChat } from "@/components/JobReviewChat";
import { api, type Channel, type ReferenceAnalysis } from "@/lib/api";

type Props = {
  onJobCreated?: (jobId: string) => void;
};

export function ReferenceShortsPanel({ onJobCreated }: Props) {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [channelId, setChannelId] = useState("");
  const [url, setUrl] = useState("https://www.youtube.com/shorts/0BKCzQGOKFI");
  const [analysis, setAnalysis] = useState<ReferenceAnalysis | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [creating, setCreating] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.channels().then(setChannels).catch(() => setError("채널 목록을 불러오지 못했습니다."));
  }, []);

  useEffect(() => {
    if (channels.length && !channelId) setChannelId(channels[0].id);
  }, [channels, channelId]);

  async function handleAnalyze() {
    if (!channelId || !url.trim()) return;
    setAnalyzing(true);
    setError(null);
    setAnalysis(null);
    setActiveJobId(null);
    try {
      const res = await api.analyzeReference(url.trim(), channelId);
      setAnalysis(res);
    } catch (e) {
      setError(e instanceof Error ? e.message.replace(/^API error: \d+ /, "") : "분석 실패");
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleCreateJob() {
    if (!channelId || !url.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const res = await api.createJobFromReference(url.trim(), channelId, analysis ?? undefined);
      setActiveJobId(res.job_id);
      onJobCreated?.(res.job_id);
    } catch (e) {
      setError(e instanceof Error ? e.message.replace(/^API error: \d+ /, "") : "Job 생성 실패");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div style={{ marginBottom: 40 }}>
      <h2 style={{ fontSize: "1.1rem", marginBottom: 8 }}>참조 Shorts로 만들기</h2>
      <p style={{ color: "var(--muted)", fontSize: "0.9rem", marginBottom: 16 }}>
        YouTube Shorts 링크를 넣으면 구조를 참고해 오리지널 대본을 만들고, 채팅으로 수정할 수 있습니다.
      </p>

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 12,
          alignItems: "center",
          marginBottom: 20,
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
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://www.youtube.com/shorts/..."
          style={{
            flex: "1 1 280px",
            minWidth: 240,
            padding: "8px 12px",
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--bg)",
            color: "inherit",
          }}
        />
        <button
          onClick={handleAnalyze}
          disabled={analyzing || !channelId}
          style={btnStyle(false)}
        >
          {analyzing ? "분석 중…" : "1. 참조 분석"}
        </button>
        <button
          onClick={handleCreateJob}
          disabled={creating || !channelId || (!analysis && !url.trim())}
          style={btnStyle(true)}
        >
          {creating ? "생성 중…" : "2. 영상 만들기"}
        </button>
      </div>

      {error && <div style={{ color: "var(--danger)", marginBottom: 16 }}>{error}</div>}

      {analysis && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "160px 1fr",
            gap: 20,
            padding: 16,
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            marginBottom: 24,
          }}
        >
          {analysis.thumbnail_url && (
            <img
              src={analysis.thumbnail_url}
              alt=""
              style={{ width: "100%", borderRadius: 8, aspectRatio: "9/16", objectFit: "cover" }}
            />
          )}
          <div>
            <div style={{ fontWeight: 700, marginBottom: 8 }}>{analysis.title}</div>
            <div style={{ fontSize: "0.85rem", color: "var(--muted)", marginBottom: 8 }}>
              {analysis.author_name} · {analysis.category}
            </div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>훅: {analysis.hook_line}</div>
            <div style={{ fontSize: "0.85rem", color: "var(--muted)", lineHeight: 1.6 }}>
              {analysis.style_notes}
            </div>
            <div style={{ marginTop: 12, fontSize: "0.8rem", color: "var(--muted)" }}>
              키워드: {analysis.keyword_cluster.join(" · ")}
            </div>
          </div>
        </div>
      )}

      {activeJobId && (
        <div
          style={{
            borderTop: "1px solid var(--border)",
            paddingTop: 24,
          }}
        >
          <h2 style={{ fontSize: "1.1rem", marginBottom: 8 }}>작업 · {activeJobId}</h2>
          <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: 16 }}>
            파이프라인 실행 후 채팅으로 대본을 수정하고 다시 렌더하세요.
          </p>
          <JobWorkspace jobId={activeJobId} />
        </div>
      )}
    </div>
  );
}

function JobWorkspace({ jobId }: { jobId: string }) {
  const [status, setStatus] = useState("TOPIC_APPROVED");

  const refreshJob = () => {
    api.job(jobId).then((j) => setStatus(j.status)).catch(() => undefined);
  };

  useEffect(() => {
    refreshJob();
  }, [jobId]);

  return (
    <>
      <JobActions jobId={jobId} status={status} onComplete={refreshJob} />
      <JobReviewChat jobId={jobId} referenceMode />
    </>
  );
}

function btnStyle(secondary: boolean): React.CSSProperties {
  return {
    padding: "8px 16px",
    borderRadius: 8,
    border: secondary ? "1px solid var(--border)" : "none",
    background: secondary ? "transparent" : "var(--accent)",
    color: secondary ? "inherit" : "#fff",
    cursor: "pointer",
    fontWeight: 600,
  };
}
