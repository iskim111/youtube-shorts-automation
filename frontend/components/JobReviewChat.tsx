"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

type Preview = {
  job_id: string;
  status: string;
  hook_line: string;
  script: Record<string, unknown> | null;
  metadata: Record<string, unknown> | null;
  reference: Record<string, unknown> | null;
  video_url: string | null;
  thumbnail_url: string | null;
  youtube_video_id: string | null;
};

type ChatMsg = { role: "user" | "assistant"; content: string };

type Props = { jobId: string; referenceMode?: boolean };

export function JobReviewChat({ jobId, referenceMode }: Props) {
  const [preview, setPreview] = useState<Preview | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(true);
  const [messages, setMessages] = useState<ChatMsg[]>([
    {
      role: "assistant",
      content: referenceMode
        ? "참조 Shorts를 바탕으로 만든 대본이에요. 채팅으로 훅·장면을 수정할 수 있습니다.\n예: `훅: 새 문장`, `장면 2: 나레이션`, `분위기를 더 코믹하게`"
        : "결과물을 확인하고 대본을 수정할 수 있어요. 예: `훅: 새 문장`, `장면 2: 나레이션`, `대본 보여줘`",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [rerunning, setRerunning] = useState(false);
  const [mediaVersion, setMediaVersion] = useState(0);

  async function loadPreview() {
    setPreviewLoading(true);
    setPreviewError(null);
    try {
      const data = (await api.jobPreview(jobId)) as Preview;
      setPreview(data);
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : "미리보기 로드 실패");
    } finally {
      setPreviewLoading(false);
    }
  }

  function resolveMediaUrl(url: string | null): string | null {
    if (!url) return null;
    if (url.startsWith("http")) return url;
    return url.startsWith("/") ? url : `/${url}`;
  }

  useEffect(() => {
    loadPreview().catch(() => undefined);
  }, [jobId]);

  async function sendMessage() {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", content: userMsg }]);
    setLoading(true);
    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const data = await api.jobChat(jobId, userMsg, history);
      setMessages((m) => [...m, { role: "assistant", content: data.reply }]);
      if (data.script) await loadPreview();
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "채팅 요청 실패" }]);
    } finally {
      setLoading(false);
    }
  }

  async function rerunPipeline() {
    setRerunning(true);
    try {
      await api.runPipeline(jobId);
      setMediaVersion((v) => v + 1);
      await loadPreview();
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "수정된 대본으로 다시 렌더했습니다. 영상을 확인하세요." },
      ]);
    } catch (e) {
      const detail = e instanceof Error ? e.message.replace(/^API error: \d+ /, "") : "재렌더 실패";
      setMessages((m) => [...m, { role: "assistant", content: `재렌더 실패: ${detail}` }]);
    } finally {
      setRerunning(false);
    }
  }

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 20,
        marginTop: 24,
      }}
    >
      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 12,
          padding: 16,
        }}
      >
        <h2 style={{ fontSize: "1rem", marginBottom: 12 }}>결과물 미리보기</h2>
        {previewLoading && (
          <div style={{ color: "var(--muted)", marginBottom: 8 }}>미리보기 불러오는 중…</div>
        )}
        {previewError && (
          <div style={{ color: "var(--danger)", marginBottom: 8, fontSize: "0.9rem" }}>
            {previewError} — 백엔드(8000) 실행 후 새로고침하세요.
          </div>
        )}
        {preview?.reference && (
          <div
            style={{
              marginBottom: 12,
              padding: 10,
              borderRadius: 8,
              background: "var(--bg)",
              fontSize: "0.8rem",
              color: "var(--muted)",
            }}
          >
            참조:{" "}
            <a
              href={String((preview.reference as { url?: string }).url ?? "")}
              target="_blank"
              rel="noreferrer"
              style={{ color: "var(--accent)" }}
            >
              {(preview.reference as { title?: string }).title ?? "Shorts"}
            </a>
          </div>
        )}
        {resolveMediaUrl(preview?.video_url ?? null) ? (
          <video
            key={mediaVersion}
            src={`${resolveMediaUrl(preview!.video_url)!}?v=${mediaVersion}`}
            controls
            poster={resolveMediaUrl(preview?.thumbnail_url ?? null) ?? undefined}
            style={{ width: "100%", maxHeight: 420, borderRadius: 8, background: "#000" }}
          />
        ) : (
          !previewLoading && (
            <div
              style={{
                height: 240,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--muted)",
                border: "1px dashed var(--border)",
                borderRadius: 8,
              }}
            >
              Run 실행 후 영상이 표시됩니다
            </div>
          )
        )}
        {preview?.metadata && (
          <div style={{ marginTop: 12, fontSize: "0.85rem", color: "var(--muted)" }}>
            제목: {(preview.metadata as { title?: string }).title}
          </div>
        )}
        {preview?.script && (
          <pre
            style={{
              marginTop: 12,
              fontSize: "0.75rem",
              color: "var(--muted)",
              whiteSpace: "pre-wrap",
              maxHeight: 180,
              overflow: "auto",
            }}
          >
            {JSON.stringify(preview.script, null, 2)}
          </pre>
        )}
        <button
          onClick={rerunPipeline}
          disabled={rerunning}
          style={{
            marginTop: 12,
            padding: "8px 14px",
            borderRadius: 8,
            border: "none",
            background: "var(--accent)",
            color: "#fff",
            cursor: rerunning ? "wait" : "pointer",
          }}
        >
          {rerunning ? "렌더 중…" : "수정 반영 후 다시 Run"}
        </button>
      </div>

      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 12,
          padding: 16,
          display: "flex",
          flexDirection: "column",
          minHeight: 480,
        }}
      >
        <h2 style={{ fontSize: "1rem", marginBottom: 12 }}>AI 채팅 수정</h2>
        <div style={{ flex: 1, overflowY: "auto", marginBottom: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          {messages.map((m, i) => (
            <div
              key={i}
              style={{
                alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                maxWidth: "90%",
                padding: "8px 12px",
                borderRadius: 8,
                background: m.role === "user" ? "var(--accent)" : "var(--bg)",
                color: m.role === "user" ? "#fff" : "inherit",
                fontSize: "0.9rem",
                whiteSpace: "pre-wrap",
              }}
            >
              {m.content}
            </div>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="훅: 새 문장 / 장면 2: ..."
            style={{
              flex: 1,
              padding: "10px 12px",
              borderRadius: 8,
              border: "1px solid var(--border)",
              background: "var(--bg)",
              color: "inherit",
            }}
          />
          <button
            onClick={sendMessage}
            disabled={loading}
            style={{
              padding: "10px 16px",
              borderRadius: 8,
              border: "none",
              background: "var(--accent)",
              color: "#fff",
              cursor: loading ? "wait" : "pointer",
            }}
          >
            전송
          </button>
        </div>
      </div>
    </div>
  );
}
