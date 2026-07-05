"use client";

import { useEffect, useState } from "react";

import { api, type ApiKeysConfig } from "@/lib/api";

const FIELDS: { key: keyof ApiKeysConfig; label: string; required?: boolean }[] = [
  { key: "openai_api_key", label: "OpenAI API Key", required: true },
  { key: "youtube_api_key", label: "YouTube Data API Key", required: true },
  { key: "elevenlabs_api_key", label: "ElevenLabs API Key", required: true },
  { key: "heygen_api_key", label: "HeyGen API Key", required: true },
  { key: "pexels_api_key", label: "Pexels API Key (선택)" },
  { key: "pixabay_api_key", label: "Pixabay API Key (선택)" },
  { key: "youtube_client_id", label: "YouTube OAuth Client ID" },
  { key: "youtube_client_secret", label: "YouTube OAuth Client Secret" },
];

export function ApiKeysForm() {
  const [form, setForm] = useState<ApiKeysConfig | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getApiKeys().then(setForm).catch(() => setError("API 키를 불러오지 못했습니다."));
  }, []);

  if (!form) return <p style={{ color: "var(--muted)" }}>로딩…</p>;

  async function save() {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await api.updateApiKeys(form);
      setForm(updated);
      setMessage("저장되었습니다.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "저장 실패");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section style={{ marginBottom: 32 }}>
      <h2 style={{ fontSize: "1rem", marginBottom: 8 }}>API 키</h2>
      <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: 16 }}>
        AI 캐릭터 영상·TOP 100·음성 생성에 필요합니다. 비어 있으면 .env 값을 사용합니다.
      </p>
      <div
        style={{
          display: "grid",
          gap: 12,
          padding: 16,
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 12,
        }}
      >
        {FIELDS.map(({ key, label }) => (
          <label key={key} style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: "0.9rem" }}>
            {label}
            <input
              type="password"
              value={(form[key] as string) || ""}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              placeholder="키 입력 (변경 없으면 비워두기)"
              style={{
                padding: "10px 12px",
                borderRadius: 8,
                border: "1px solid var(--border)",
                background: "var(--bg)",
                color: "inherit",
              }}
            />
          </label>
        ))}
        <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: "0.9rem" }}>
          영상 모드
          <select
            value={form.video_mode}
            onChange={(e) => setForm({ ...form, video_mode: e.target.value })}
            style={{ padding: "10px 12px", borderRadius: 8, background: "var(--bg)", color: "inherit" }}
          >
            <option value="ai_character">AI 캐릭터 (HeyGen)</option>
            <option value="stock_broll">스톡 B-roll</option>
          </select>
        </label>
        {form.configured && (
          <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
            {Object.entries(form.configured)
              .map(([k, v]) => `${k}: ${v ? "✓" : "✗"}`)
              .join(" · ")}
          </div>
        )}
        <button
          type="button"
          onClick={save}
          disabled={saving}
          style={{
            padding: "10px 16px",
            borderRadius: 8,
            border: "none",
            background: "var(--accent)",
            color: "#fff",
            fontWeight: 600,
            cursor: saving ? "wait" : "pointer",
            width: "fit-content",
          }}
        >
          {saving ? "저장 중…" : "API 키 저장"}
        </button>
        {message && <p style={{ color: "var(--success)", fontSize: "0.85rem" }}>{message}</p>}
        {error && <p style={{ color: "var(--danger)", fontSize: "0.85rem" }}>{error}</p>}
      </div>
    </section>
  );
}
