'use client';

import * as Sentry from '@sentry/nextjs';
import { useEffect } from 'react';

export default function SentryMonitor() {
  // Verify Sentry is configured properly on component mount
  useEffect(() => {
    // Check if Sentry DSN is configured
    const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
    console.log('SENTRY CONFIG CHECK - DSN configured:', !!dsn);

    // Test Sentry by sending a test event
    if (dsn) {
      try {
        // Send a test message to Sentry to verify the connection
        Sentry.captureMessage('Sentry Connection Test', {
          level: 'info',
          tags: {
            test: 'connection',
            environment: process.env.NODE_ENV || 'unknown'
          }
        });
        console.log('SENTRY TEST - Test message sent to Sentry');
      } catch (error) {
        console.error('SENTRY TEST - Failed to send test message:', error);
      }
    }
  }, []);

  // This component doesn't render anything visible
  return null;
}
