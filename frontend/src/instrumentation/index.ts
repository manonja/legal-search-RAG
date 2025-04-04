// This file is for server-side instrumentation

export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const Sentry = await import("@sentry/nextjs");

    Sentry.init({
      dsn: process.env.NEXT_PUBLIC_SENTRY_DSN || process.env.SENTRY_DSN,

      // Set tracesSampleRate to 1.0 to capture 100% of transactions for performance monitoring
      // Adjust in production as needed
      tracesSampleRate: 1.0,

      // Environment will be derived from NODE_ENV
      environment: process.env.NODE_ENV,

      // Version taken from environment variable
      release: process.env.NEXT_PUBLIC_VERSION || "0.1.0",
    });
  }
}
