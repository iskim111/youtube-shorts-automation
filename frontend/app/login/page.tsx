"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";

import { api } from "@/lib/api";
import { isAuthEnabled, setAuthToken } from "@/lib/auth";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") ?? "/overview";
  const [email, setEmail] = useState("admin@localhost");
  const [password, setPassword] = useState("admin1234");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isAuthEnabled()) {
    return (
      <p style={{ color: "var(--muted)" }}>
        인증이 비활성화되어 있습니다.{" "}
        <a href="/overview" style={{ color: "var(--accent)" }}>
          대시보드로 이동
        </a>
      </p>
    );
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await api.login(email, password);
      setAuthToken(result.access_token);
      router.replace(next);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "로그인 실패");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: "0.9rem" }}>
        이메일
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={inputStyle}
        />
      </label>
      <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: "0.9rem" }}>
        비밀번호
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={inputStyle}
        />
      </label>
      {error && <p style={{ color: "var(--danger)", fontSize: "0.85rem" }}>{error}</p>}
      <button type="submit" disabled={loading} style={buttonStyle}>
        {loading ? "로그인 중…" : "로그인"}
      </button>
    </form>
  );
}

const inputStyle: React.CSSProperties = {
  padding: "10px 12px",
  borderRadius: 8,
  border: "1px solid var(--border)",
  background: "var(--bg)",
  color: "var(--text)",
};

const buttonStyle: React.CSSProperties = {
  padding: "12px 16px",
  borderRadius: 8,
  border: "none",
  background: "var(--accent)",
  color: "#fff",
  fontWeight: 600,
  cursor: "pointer",
};

export default function LoginPage() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 400,
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 16,
          padding: 32,
        }}
      >
        <h1 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: 8 }}>Shorts Automation</h1>
        <p style={{ color: "var(--muted)", fontSize: "0.9rem", marginBottom: 24 }}>
          운영 대시보드 로그인
        </p>
        <Suspense fallback={<p style={{ color: "var(--muted)" }}>로딩…</p>}>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}
