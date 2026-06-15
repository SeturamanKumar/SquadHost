import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: 'export',
  images: { unoptimized: true },
  allowedDevOrigins: ['::'],
};

module.exports = {
}

export default nextConfig;
