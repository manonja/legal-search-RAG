/** @type {import('next').Config} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: [],
  },
  // Make sure environment variables are available
  env: {
    // Pass through API URL from environment or use a default
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    // Ensure PORT is a string
    PORT: process.env.PORT ? String(process.env.PORT) : "3000",
  },
};

module.exports = nextConfig;
