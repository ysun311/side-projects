import type { NextConfig } from "next";

const allowedDevOrigins = process.env.ALLOWED_DEV_ORIGINS?.split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

const nextConfig: NextConfig = allowedDevOrigins?.length
  ? { allowedDevOrigins }
  : {};

export default nextConfig;
