"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api } from "@/lib/api";

const TEMPLATES = [
  { id: "bold_center", label: "Bold Center" },
  { id: "split_hook", label: "Split Hook" },
  { id: "minimal_bottom", label: "Minimal Bottom" },
];

type Props = {
  jobId: string;
  currentTemplate: string;
};

export function JobSchedule({ jobId, currentTemplate }: Props) {
  const router = useRouter();
  const [template, setTemplate] = useState(currentTemplate);
  const [datetime, setDatetime] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function handleSchedule() {
    if (!datetime) return;
    setLoading(true);
    setMsg(null);
    try {
      const iso = new Date(datetime).toISOString();
      await api.scheduleJob(jobId, iso, template);
      setMsg("예약 완료");
      router.refresh();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "예약 실패");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        marginTop: 24,
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 12,
        padding: 20,
      }}
    >
      <h2 style={{ fontSize: "1rem", marginBottom: 12 }}>예약 & 렌더 템플릿</h2>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end" }}>
        <label style={{ fontSize: "0.85rem" }}>
          템플릿
          <select
            value={template}
            onChange={(e) => setTemplate(e.target.value)}
            style={{
              display: "block",
              marginTop: 4,
              padding: "8px 12px",
              borderRadius: 6,
              background: "var(--bg)",
              color: "var(--text)",
              border: "1px solid var(--border)",
            }}
          >
            {TEMPLATES.map((t) => (
              <option key={t.id} value={t.id}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
        <label style={{ fontSize: "0.85rem" }}>
          게시 예약
          <input
            type="datetime-local"
            value={datetime}
            onChange={(e) => setDatetime(e.target.value)}
            style={{
              display: "block",
              marginTop: 4,
              padding: "8px 12px",
              borderRadius: 6,
              background: "var(--bg)",
              color: "var(--text)",
              border: "1px solid var(--border)",
            }}
          />
        </label>
        <button
          onClick={handleSchedule}
          disabled={loading || !datetime}
          style={{
            padding: "10px 16px",
            borderRadius: 8,
            border: "none",
            background: "var(--accent)",
            color: "#fff",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          {loading ? "저장 중…" : "예약 저장"}
        </button>
      </div>
      {msg && (
        <p style={{ marginTop: 8, fontSize: "0.85rem", color: "var(--success)" }}>
          {msg}
        </p>
      )}
    </div>
  );
}
