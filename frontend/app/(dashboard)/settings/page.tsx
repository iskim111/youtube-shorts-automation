import { Suspense } from "react";

import { ChannelCreateForm } from "@/components/ChannelCreateForm";
import { OAuthConnect } from "@/components/OAuthConnect";
import { SetupChecklist } from "@/components/SetupChecklist";import { api, type Channel } from "@/lib/api";

export default async function SettingsPage() {
  let channels: Channel[] = [];
  let error: string | null = null;

  try {
    channels = await api.channels();
  } catch (e) {
    error = e instanceof Error ? e.message : "API 연결 실패";
  }

  return (
    <div>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 8 }}>Settings</h1>
      <p style={{ color: "var(--muted)", marginBottom: 32 }}>
        YouTube OAuth 채널 연결 · Semi-auto 업로드 준비
      </p>

      {error && (
        <div style={{ color: "var(--danger)", marginBottom: 24 }}>백엔드 미연결: {error}</div>
      )}

      <SetupChecklist />

      <section style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: "1rem", marginBottom: 16 }}>채널 관리</h2>
        <ChannelCreateForm />
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: "1rem", marginBottom: 16 }}>YouTube 연동</h2>        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: 20,
            marginBottom: 16,
            fontSize: "0.85rem",
            color: "var(--muted)",
            lineHeight: 1.7,
          }}
        >
          <p>Google Cloud Console에서 OAuth 클라이언트를 생성하고 아래를 설정하세요.</p>
          <ul style={{ marginTop: 8, paddingLeft: 20 }}>
            <li>
              Redirect URI:{" "}
              <code>http://localhost:8000/api/v1/channels/oauth/callback</code>
            </li>
            <li>Scope: youtube.upload, youtube.readonly</li>
            <li>환경변수: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET</li>
          </ul>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {channels.map((channel) => (
            <Suspense key={channel.id} fallback={<div>로딩…</div>}>
              <OAuthConnect channel={channel} />
            </Suspense>
          ))}
          {channels.length === 0 && !error && (
            <p style={{ color: "var(--muted)" }}>등록된 채널이 없습니다.</p>
          )}
        </div>
      </section>
    </div>
  );
}
