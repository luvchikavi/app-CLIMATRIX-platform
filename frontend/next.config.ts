import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Disable Turbopack for production builds (use webpack instead)
  experimental: {
    turbo: false,
  },
};

export default nextConfig;
