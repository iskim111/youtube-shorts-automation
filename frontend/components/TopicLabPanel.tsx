"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, type Channel, type TopicCandidate } from "@/lib/api";

const SOURCE_LABEL: Record<string, string> = {
  trending: "트렌드",
  ai: "AI 추천",
  mixed: "혼합",
  template: "기본",
};

export function TopicLabPanel() {
  const router = useRouter();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [channelId, setChannelId] = useState("");
  const [source, setSource] = useState<"trending" | "ai" | "mixed">("mixed");
  const [topics, setTopics] = useState<TopicCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [approving, setApproving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.channels().then(setChannels).catch(() => setError("채널 목록을 불러오지 못했습니다."));
  }, []);

  useEffect(() => {
    if (channels.length && !channelId) {
      const oauth = channels.find((c) => c.oauth_connected) ?? channels[0];
      setChannelId(oauth.id);
    }
  }, [channels, channelId]);

  async function handleGenerate() {
    if (!channelId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/topics/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel_id: channelId, limit: 8, source }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = (await res.json()) as TopicCandidate[];
      setTopics(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "주제 생성 실패");
    } finally {
      setLoading(false);
    }
  }

  async function handleSelect(topicId: string) {
    setApproving(topicId);
    try {
      const res = await api.approveTopic(topicId);
      router.push(`/jobs/${res.job_id}`);
    } catch {
      setError("주제 승인 실패");
      setApproving(null);
    }
  }

  return (
    <div style={{ marginBottom: 32 }}>
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
        <select
          value={source}
          onChange={(e) => setSource(e.target.value as typeof source)}
          style={{ padding: "8px 12px", borderRadius: 8, background: "var(--bg)", color: "inherit" }}
        >
          <option value="mixed">혼합 (트렌드+AI)</option>
          <option value="trending">트렌드 (무료·조회 잠재력 높음)</option>
          <option value="ai">AI 추천 (키 없으면 무료 변형)</option>
        </select>
        <button
          onClick={handleGenerate}
          disabled={loading || !channelId}
          style={{
            padding: "8px 16px",
            borderRadius: 8,
            border: "none",
            background: "var(--accent)",
            color: "#fff",
            cursor: loading ? "wait" : "pointer",
          }}
        >
          {loading ? "생성 중…" : "주제 목록 생성"}
        </button>
        <span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
          원하는 주제를 선택하면 Job이 생성됩니다
        </span>
      </div>

      {error && <div style={{ color: "var(--danger)", marginBottom: 16 }}>{error}</div>}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
        {topics.map((t) => (
          <div
            key={t.id}
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 12,
              padding: 16,
              display: "flex",
              flexDirection: "column",
              gap: 10,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span className="badge badge-success">{SOURCE_LABEL[t.topic_source] ?? t.topic_source}</span>
              <span style={{ fontWeight: 700 }}>{t.scores.final}점</span>
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
              {t.category} · 조회잠재 {t.scores.view_potential}
            </div>
            <div style={{ fontWeight: 600, lineHeight: 1.4, flex: 1 }}>{t.hook_line}</div>
            <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{t.keyword_cluster.join(" · ")}</div>
            <button
              onClick={() => handleSelect(t.id)}
              disabled={approving === t.id}
              style={{
                padding: "8px 12px",
                borderRadius: 8,
                border: "none",
                background: "var(--accent)",
                color: "#fff",
                cursor: approving ? "wait" : "pointer",
              }}
            >
              {approving === t.id ? "생성 중…" : "이 주제로 만들기"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
