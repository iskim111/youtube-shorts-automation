type StatCardProps = {
  label: string;
  value: string | number;
  sub?: string;
};

export function StatCard({ label, value, sub }: StatCardProps) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 12,
        padding: "20px 24px",
      }}
    >
      <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: "1.75rem", fontWeight: 700 }}>{value}</div>
      {sub && <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: 4 }}>{sub}</div>}
    </div>
  );
}
