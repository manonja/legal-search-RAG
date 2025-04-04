/** @type {import('next').NextConfig} */
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
    // Additional webpack configurations if needed
    return config;
  },

  // Specify the output mode
  output: "standalone",

  // Setting a proper production assetPrefix
  assetPrefix: undefined, // Let Next.js decide based on the deployment environment

  // Configure server to listen on all network interfaces
  experimental: {
    serverComponentsExternalPackages: [],
  },

  // Add proper handling for trailing slash and path resolution
  trailingSlash: false,

  // Configure image optimization and domains
  images: {
    unoptimized: process.env.NODE_ENV === "development",
    domains: ["*"],
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
};

module.exports = nextConfig;
