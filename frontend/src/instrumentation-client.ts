// This file is for client-side instrumentation
// It follows Next.js recommendations for handling client-side instrumentation

import * as Sentry from '@sentry/nextjs';

// Check if Sentry DSN is configured
const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
if (dsn) {
  console.log('Sentry Client DSN is configured');
} else {
  console.warn('Sentry Client DSN is missing - errors will not be reported to Sentry');
}

Sentry.init({
  dsn: dsn,

  // Adjust this value in production, or use tracesSampler for greater control
  tracesSampleRate: 1.0,

  // Setting this option to true will print useful information to the console while you're setting up Sentry.
  debug: process.env.NODE_ENV === 'development' || process.env.DEBUG_SENTRY === 'true',

  // Enable Replay for error monitoring
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,

  // Enable browser tracing integration
  integrations: [
    Sentry.replayIntegration({
      // Additional SDK configuration goes in here, for example:
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],

  // Environment will be derived from NODE_ENV
  environment: process.env.NODE_ENV || 'development',

  // Version taken from environment variable
  release: process.env.NEXT_PUBLIC_VERSION || '0.1.0',
});
