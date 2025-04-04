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
    // Ensure PORT is a string
    PORT: process.env.PORT ? String(process.env.PORT) : "3000",
  },
  // This ensures Next.js allows the environment variables to be used in the client-side code
  publicRuntimeConfig: {
    apiUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    apiToken: process.env.NEXT_PUBLIC_API_TOKEN || "test",
  },
  experimental: {
    // Enable the instrumentation hook for Sentry
    instrumentationHook: true,
  },
};

// Import Sentry config wrapper
const { withSentryConfig } = require("@sentry/nextjs");

// Sentry webpack plugin options
const sentryWebpackPluginOptions = {
  // Silent to reduce noise in the console during builds
  silent: true,
};

// Export the config with Sentry integration
module.exports = withSentryConfig(nextConfig, sentryWebpackPluginOptions);
