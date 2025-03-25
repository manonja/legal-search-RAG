/** @type {import('next').Config} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: [],
  },
  // Make sure environment variables are available
  env: {
    // Pass through the API URL as-is, without modification
    // The client-side code will handle the proper formatting
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    PORT: process.env.PORT || 3000,
  },
  // This ensures Next.js allows the environment variables to be used in the client-side code
  publicRuntimeConfig: {
    apiUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
};

module.exports = nextConfig;
