/**
 * Health check endpoint for Cloud Run
 * Used for liveness and startup probes
 */

export async function GET() {
  return Response.json({ status: "ok" });
}
