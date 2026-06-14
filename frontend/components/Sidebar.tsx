"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { clearAuthToken, isAuthEnabled } from "@/lib/auth";
const NAV = [
  { href: "/overview", label: "Overview" },
  { href: "/topics", label: "Topic Lab" },
  { href: "/calendar", label: "Upload Calendar" },
  { href: "/rights", label: "Rights Center" },
  { href: "/analytics", label: "Analytics" },
  { href: "/audit", label: "Audit" },
  { href: "/settings", label: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const authOn = isAuthEnabled();

  function logout() {
    clearAuthToken();
    router.push("/login");
    router.refresh();
  }
  return (
    <aside
      style={{
        width: 220,
        minHeight: "100vh",
        background: "var(--surface)",
        borderRight: "1px solid var(--border)",
        padding: "24px 16px",
      }}
    >
      <div style={{ marginBottom: 32 }}>
        <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>Shorts Automation</div>
        <div style={{ fontWeight: 700, fontSize: "1.1rem" }}>운영 대시보드</div>
        <div
          style={{
            marginTop: 8,
            fontSize: "0.75rem",
            color: "var(--accent)",
            fontWeight: 600,
          }}
        >
          Semi-auto
        </div>
      </div>
      <nav style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {NAV.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              style={{
                padding: "10px 12px",
                borderRadius: 8,
                fontSize: "0.9rem",
                background: active ? "rgba(255,68,68,0.12)" : "transparent",
                color: active ? "var(--accent)" : "var(--text)",
              }}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      {authOn && (
        <button
          type="button"
          onClick={logout}
          style={{
            marginTop: 24,
            width: "100%",
            padding: "10px 12px",
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "transparent",
            color: "var(--muted)",
            cursor: "pointer",
            fontSize: "0.85rem",
          }}
        >
          로그아웃
        </button>
      )}
    </aside>
  );
}