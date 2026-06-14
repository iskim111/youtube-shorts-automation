"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { api } from "@/lib/api";

export function ChannelCreateForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await api.createChannel({ name: name.trim() });
      setName("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "채널 생성 실패");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      style={{
        display: "flex",
        gap: 12,
        alignItems: "flex-end",
        flexWrap: "wrap",
        marginBottom: 24,
      }}
    >
      <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: "0.9rem" }}>
        새 채널 이름
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="예: 코미디 쇼츠"
          style={{
            padding: "10px 12px",
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--bg)",
            color: "var(--text)",
            minWidth: 220,
          }}
        />
      </label>
      <button
        type="submit"
        disabled={loading || !name.trim()}
        style={{
          padding: "10px 16px",
          borderRadius: 8,
          border: "none",
          background: "var(--accent)",
          color: "#fff",
          fontWeight: 600,
          cursor: loading ? "wait" : "pointer",
        }}
      >
        {loading ? "생성 중…" : "채널 추가"}
      </button>
      {error && (
        <p style={{ width: "100%", color: "var(--danger)", fontSize: "0.85rem" }}>{error}</p>
      )}
    </form>
  );
}
