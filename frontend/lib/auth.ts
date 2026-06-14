const TOKEN_COOKIE = "auth_token";
const AUTH_ENABLED = process.env.NEXT_PUBLIC_AUTH_ENABLED === "true";

export function isAuthEnabled(): boolean {
  return AUTH_ENABLED;
}

export function setAuthToken(token: string): void {
  if (typeof document === "undefined") return;
  const maxAge = 60 * 60 * 8;
  document.cookie = `${TOKEN_COOKIE}=${encodeURIComponent(token)}; path=/; max-age=${maxAge}; SameSite=Lax`;
  localStorage.setItem(TOKEN_COOKIE, token);
}

export function clearAuthToken(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${TOKEN_COOKIE}=; path=/; max-age=0`;
  localStorage.removeItem(TOKEN_COOKIE);
}

export function getClientAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  const fromStorage = localStorage.getItem(TOKEN_COOKIE);
  if (fromStorage) return fromStorage;
  const match = document.cookie
    .split(";")
    .map((c) => c.trim())
    .find((c) => c.startsWith(`${TOKEN_COOKIE}=`));
  if (!match) return null;
  return decodeURIComponent(match.slice(TOKEN_COOKIE.length + 1));
}

export async function getServerAuthToken(): Promise<string | null> {
  if (!AUTH_ENABLED) return null;
  const { cookies } = await import("next/headers");
  const value = (await cookies()).get(TOKEN_COOKIE)?.value;
  return value ? decodeURIComponent(value) : null;
}
