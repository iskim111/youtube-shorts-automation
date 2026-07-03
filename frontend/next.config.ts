import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${api}/api/v1/:path*`,
      },
      {
        source: "/media/:path*",
        destination: `${api}/media/:path*`,
      },
    ];
  },
};

export default nextConfig;
