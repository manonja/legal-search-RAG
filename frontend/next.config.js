/** @type {import('next').NextConfig} */
const { withSentryConfig } = require("@sentry/nextjs");

const nextConfig = {
  // Enable React strict mode for better development experience
  reactStrictMode: true,

  // Disable image optimization during development
  // In production, consider using a CDN or configure with GCP Cloud Storage
  images: {
    unoptimized: process.env.NODE_ENV === "development",
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },

  // Configure environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_ENVIRONMENT:
      process.env.NEXT_PUBLIC_ENVIRONMENT || "development",
  },

  // Enable faster refresh during development
  webpack: (config, { dev, isServer }) => {
    // Only include firebase-admin in the server bundle
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        // Provide polyfills for Node.js modules used by Firebase Admin SDK
        fs: false,
        path: false,
        os: false,
        net: false,
        tls: false,
        child_process: false,
        process: false,
        crypto: false,
      };
    }

    // Additional webpack configurations if needed
    return config;
  },

  // Specify the output mode
  output: "standalone",

  // Setting a proper production assetPrefix
  assetPrefix: undefined, // Let Next.js decide based on the deployment environment

  // Configure server to listen on all network interfaces
  experimental: {
    serverComponentsExternalPackages: ['firebase-admin'], // Ensure firebase-admin is treated as external in Server Components
    // Enable instrumentation hook for Sentry
    instrumentationHook: true,
  },

  // Add proper handling for trailing slash and path resolution
  trailingSlash: false,

  // Configure image optimization and domains
  images: {
    unoptimized: process.env.NODE_ENV === "development",
    domains: ["*"], // Deprecated but keeping for backward compatibility
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
};

// Sentry webpack plugin options
const sentryWebpackPluginOptions = {
  // Additional options for the Sentry webpack plugin
  org: process.env.SENTRY_ORG || "unknown",
  project: process.env.SENTRY_PROJECT || "legal-search-rag",
  silent: true, // Suppresses all logs
  // For all available options, see:
  // https://github.com/getsentry/sentry-webpack-plugin#options
  // Hide source maps from generated client builds
  hideSourceMaps: process.env.NODE_ENV === "production",
  // Automatically instrument SDK with Next.js routing and performance monitoring
  autoInstrumentServerFunctions: true,
  autoInstrumentMiddleware: true,
  tunnelRoute: "/monitoring",
};

// Export the Next.js config wrapped with Sentry
module.exports = withSentryConfig(
  nextConfig,
  sentryWebpackPluginOptions
);
