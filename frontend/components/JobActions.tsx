"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api } from "@/lib/api";

type Props = {
  jobId: string;
  status: string;
};

export function JobActions({ jobId, status }: Props) {
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleRun() {
    setLoading("run");
    setError(null);
    setMessage(null);
    try {
      const res = await api.runPipeline(jobId);
      setMessage(res.message);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "실행 실패");
    } finally {
      setLoading(null);
    }
  }

  async function handleRetry() {
    setLoading("retry");
    setError(null);
    try {
      await api.retryJob(jobId);
      setMessage("재시도 완료");
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "재시도 실패");
    } finally {
      setLoading(null);
    }
  }

  async function handlePublish() {
    setLoading("publish");
    setError(null);
    setMessage(null);
    try {
      const res = await api.publishJob(jobId);
      const label = res.dry_run ? "(dry-run)" : "";
      setMessage(`업로드 완료 ${label}: ${res.youtube_video_id}`);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "업로드 실패");
    } finally {
      setLoading(null);
    }
  }

  const canRun = ["TOPIC_APPROVED", "SCRIPT_READY", "QA_HOLD", "RIGHTS_HOLD"].includes(status);
  const canPublish = ["QA_PENDING", "QA_APPROVED", "UPLOAD_FAILED"].includes(status);
  const canRetry = status === "UPLOAD_FAILED";

  return (
    <div style={{ marginTop: 24 }}>
      <h2 style={{ fontSize: "1.1rem", marginBottom: 12 }}>Semi-auto 제어</h2>

      {message && (
        <div
          style={{
            background: "rgba(52,199,89,0.1)",
            border: "1px solid var(--success)",
            borderRadius: 8,
            padding: 12,
            marginBottom: 12,
            color: "var(--success)",
            fontSize: "0.9rem",
          }}
        >
          {message}
        </div>
      )}
      {error && (
        <div
          style={{
            background: "rgba(255,69,58,0.1)",
            border: "1px solid var(--danger)",
            borderRadius: 8,
            padding: 12,
            marginBottom: 12,
            color: "var(--danger)",
            fontSize: "0.9rem",
          }}
        >
          {error}
        </div>
      )}

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        {canRun && (
          <button
            onClick={handleRun}
            disabled={loading !== null}
            style={btnStyle("var(--accent)", "#fff")}
          >
            {loading === "run" ? "생성 중…" : "1. 파이프라인 실행 (대본→렌더)"}
          </button>
        )}
        {canPublish && (
          <button
            onClick={handlePublish}
            disabled={loading !== null}
            style={btnStyle("var(--success)", "#fff")}
          >
            {loading === "publish" ? "업로드 중…" : "2. QA 승인 & 업로드"}
          </button>
        )}
        {canRetry && (
          <button
            onClick={handleRetry}
            disabled={loading !== null}
            style={btnStyle("transparent", "var(--warning)")}
          >
            {loading === "retry" ? "재시도 중…" : "기술 오류 재시도"}
          </button>
        )}
        {status === "PUBLISHED" && (
          <span className="badge badge-success">게시 완료</span>
        )}
      </div>

      <p style={{ color: "var(--muted)", fontSize: "0.8rem", marginTop: 12 }}>
        기본 dry-run 모드: PILOT_DRY_RUN_UPLOAD=true 시 YouTube 실제 업로드 없이 시뮬레이션
      </p>
    </div>
  );
}

function btnStyle(bg: string, color: string): React.CSSProperties {
  return {
    padding: "10px 20px",
    borderRadius: 8,
    border: bg === "transparent" ? `1px solid ${color}` : "none",
    background: bg,
    color,
    fontWeight: 600,
    cursor: "pointer",
  };
}
