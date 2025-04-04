// This file is for client-side instrumentation

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN || process.env.SENTRY_DSN,

  // Enable replay for client-side error tracking
  integrations: [Sentry.replayIntegration()],

  // Set tracesSampleRate to 1.0 to capture 100% of transactions for performance monitoring
  // Adjust in production as needed
  tracesSampleRate: 1.0,

  // Capture Replay for 10% of all sessions, plus 100% of sessions with an error
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,

  // Environment will be derived from NODE_ENV
  environment: process.env.NODE_ENV,

  // Version taken from environment variable
  release: process.env.NEXT_PUBLIC_VERSION || "0.1.0",
});
