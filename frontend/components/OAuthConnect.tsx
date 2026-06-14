"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { api, type Channel } from "@/lib/api";

type Props = {
  channel: Channel;
};

export function OAuthConnect({ channel }: Props) {
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [connected, setConnected] = useState(channel.oauth_connected);
  const [ytTitle, setYtTitle] = useState(channel.youtube_channel_title);
  const [ytId, setYtId] = useState(channel.youtube_channel_id);

  const refreshStatus = useCallback(async () => {
    try {
      const status = await api.oauthStatus(channel.id);
      setConnected(status.connected);
      setYtTitle(status.youtube_channel_title);
      setYtId(status.youtube_channel_id);
    } catch {
      /* ignore */
    }
  }, [channel.id]);

  useEffect(() => {
    if (searchParams.get("oauth") === "success") {
      const title = searchParams.get("youtube_channel_title");
      setSuccessMsg(title ? `YouTube 연결 완료: ${decodeURIComponent(title)}` : "YouTube 연결 완료");
      refreshStatus();
    }
  }, [searchParams, refreshStatus]);

  async function handleConnect() {
    setLoading(true);
    setError(null);
    try {
      const { authorization_url } = await api.oauthStart(channel.id);
      window.location.href = authorization_url;
    } catch (e) {
      setError(e instanceof Error ? e.message : "연결 시작 실패");
      setLoading(false);
    }
  }

  async function handleDisconnect() {
    setLoading(true);
    setError(null);
    try {
      await api.oauthDisconnect(channel.id);
      setConnected(false);
      setYtTitle(null);
      setYtId(null);
      setSuccessMsg("YouTube 연결이 해제되었습니다.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "연결 해제 실패");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 12,
        padding: 24,
      }}
    >
      <h2 style={{ fontSize: "1.1rem", marginBottom: 8 }}>{channel.name}</h2>
      <p style={{ color: "var(--muted)", fontSize: "0.9rem", marginBottom: 16 }}>
        운영 모드: {channel.operation_mode} · 일일 업로드 캡: {channel.daily_upload_cap}
      </p>

      {successMsg && (
        <div
          style={{
            background: "rgba(52,199,89,0.1)",
            border: "1px solid var(--success)",
            borderRadius: 8,
            padding: 12,
            marginBottom: 16,
            color: "var(--success)",
            fontSize: "0.9rem",
          }}
        >
          {successMsg}
        </div>
      )}

      {error && (
        <div
          style={{
            background: "rgba(255,69,58,0.1)",
            border: "1px solid var(--danger)",
            borderRadius: 8,
            padding: 12,
            marginBottom: 16,
            color: "var(--danger)",
            fontSize: "0.9rem",
          }}
        >
          {error}
        </div>
      )}

      <div style={{ marginBottom: 20 }}>
        {connected ? (
          <>
            <span className="badge badge-success">연결됨</span>
            {ytTitle && (
              <div style={{ marginTop: 12, fontSize: "0.95rem" }}>
                <strong>{ytTitle}</strong>
                {ytId && (
                  <div style={{ color: "var(--muted)", fontSize: "0.8rem", marginTop: 4 }}>
                    Channel ID: {ytId}
                  </div>
                )}
              </div>
            )}
          </>
        ) : (
          <span className="badge badge-muted">미연결</span>
        )}
      </div>

      {connected ? (
        <button
          onClick={handleDisconnect}
          disabled={loading}
          style={{
            padding: "10px 20px",
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "transparent",
            color: "var(--text)",
            cursor: loading ? "wait" : "pointer",
          }}
        >
          {loading ? "처리 중…" : "연결 해제"}
        </button>
      ) : (
        <button
          onClick={handleConnect}
          disabled={loading}
          style={{
            padding: "10px 20px",
            borderRadius: 8,
            border: "none",
            background: "var(--accent)",
            color: "#fff",
            fontWeight: 600,
            cursor: loading ? "wait" : "pointer",
          }}
        >
          {loading ? "이동 중…" : "YouTube 채널 연결"}
        </button>
      )}
    </div>
  );
}
