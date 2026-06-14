import { api, type SetupStatus } from "@/lib/api";

function CheckRow({ ok, label, detail, warning }: { ok: boolean; label: string; detail: string; warning?: boolean }) {
  const color = ok ? (warning ? "var(--warning)" : "var(--success)") : "var(--danger)";
  const mark = ok ? (warning ? "!" : "✓") : "✗";
  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        padding: "12px 0",
        borderBottom: "1px solid var(--border)",
        fontSize: "0.9rem",
      }}
    >
      <span style={{ color, fontWeight: 700, width: 20 }}>{mark}</span>
      <div>
        <div style={{ fontWeight: 600 }}>{label}</div>
        <div style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: 2 }}>{detail}</div>
      </div>
    </div>
  );
}

export async function SetupChecklist() {
  let setup: SetupStatus | null = null;
  let error: string | null = null;

  try {
    setup = await api.setupStatus();
  } catch (e) {
    error = e instanceof Error ? e.message : "API 연결 실패";
  }

  if (error) {
    return <p style={{ color: "var(--danger)" }}>설정 점검 불가: {error}</p>;
  }
  if (!setup) return null;

  return (
    <section style={{ marginBottom: 32 }}>
      <h2 style={{ fontSize: "1rem", marginBottom: 8 }}>운영 준비 체크리스트</h2>
      <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: 16 }}>
        {setup.ready_for_real_upload
          ? "실제 YouTube 업로드 준비 완료"
          : "Dry-run 파일럿 가능 · 실제 업로드는 아래 항목을 완료하세요"}
      </p>
      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 12,
          padding: "8px 20px",
        }}
      >
        {setup.checks.map((c) => (
          <CheckRow key={c.id} ok={c.ok} label={c.label} detail={c.detail} warning={c.warning} />
        ))}
      </div>
      {setup.redirect_uri && (
        <p style={{ color: "var(--muted)", fontSize: "0.8rem", marginTop: 12 }}>
          OAuth Redirect URI: <code>{setup.redirect_uri}</code>
        </p>
      )}
    </section>
  );
}
