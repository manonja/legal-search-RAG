"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

export default function GlobalError({ error, reset }) {
  useEffect(() => {
    // Log the error to Sentry
    Sentry.captureException(error);
  }, [error]);

  return (
    <html>
      <body>
        <div className="flex flex-col items-center justify-center min-h-screen p-5 text-center">
          <h2 className="text-2xl font-bold mb-4">Something went wrong!</h2>
          <p className="mb-6">
            We've been notified and are working to fix the issue.
          </p>
          <button
            className="px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-700"
            onClick={() => reset()}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
