import { getApplicationVersion } from "@/lib/getApplicationVersion";
import { getSystemDiagnostics } from "@/lib/getSystemDiagnostics";
import { NextResponse } from "next/server";

// This could be set to 'edge' if the app uses Edge Runtime, but leaving as Node.js default
// export const runtime = 'edge';

interface HealthResponse {
  status: "ok" | "degraded";
  timestamp: string;
  version: string;
  environment: string;
  details?: string;
  diagnostics?: {
    memoryUsage: string;
    uptime: string;
    nodeVersion: string;
  };
}

/**
 * GET handler for the /api/health endpoint
 * Returns information about the application's health status
 */
export async function GET(): Promise<NextResponse<HealthResponse>> {
  // Get the application version from either env var override or package.json/VERSION file
  const version =
    process.env.HEALTH_CHECK_VERSION_OVERRIDE ||
    getApplicationVersion() ||
    "0.0.0";

  // Get the current environment
  const environment = process.env.NODE_ENV || "development";

  // Create the base response
  const response: HealthResponse = {
    status: "ok", // Default status
    timestamp: new Date().toISOString(),
    version,
    environment,
  };

  // Check if app is in a degraded state (this is a placeholder for actual health checks)
  // In a real application, you would add additional checks here
  const isHealthy = true; // Replace with actual health checks

  if (!isHealthy) {
    response.status = "degraded";
    response.details = "Application is in a degraded state"; // Customize this message
  }

  // Add diagnostics for non-production environments if not disabled
  if (
    environment !== "production" &&
    process.env.HEALTH_CHECK_DISABLE_DIAGNOSTICS !== "true"
  ) {
    response.diagnostics = getSystemDiagnostics();
  }

  // Return the response with appropriate status code
  return NextResponse.json(response, {
    status: 200, // Always return 200 even if degraded per requirements
    headers: {
      "Content-Type": "application/json",
    },
  });
}

// Disable all other HTTP methods for this endpoint
export async function POST() {
  return new Response(null, { status: 405 });
}

export async function PUT() {
  return new Response(null, { status: 405 });
}

export async function DELETE() {
  return new Response(null, { status: 405 });
}

export async function PATCH() {
  return new Response(null, { status: 405 });
}
