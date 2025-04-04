/**
 * @jest-environment node
 */

import { GET } from "@/app/api/health/route";
import { getApplicationVersion } from "@/lib/getApplicationVersion";

// Mock the getApplicationVersion function
jest.mock("@/lib/getApplicationVersion", () => ({
  getApplicationVersion: jest.fn(),
}));

// Mock the getSystemDiagnostics function
jest.mock("@/lib/getSystemDiagnostics", () => ({
  getSystemDiagnostics: jest.fn().mockReturnValue({
    memoryUsage: "100MB",
    uptime: "1h 30m",
    nodeVersion: "v20.0.0",
  }),
}));

// Mock Next.js process.env
jest.mock("next/headers", () => ({
  headers: jest.fn(),
}));

describe("/api/health endpoint", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    // Reset environment variables and mocks before each test
    jest.resetModules();
    // Create a new object to avoid modifying read-only properties
    process.env = {
      ...originalEnv,
      NODE_ENV: originalEnv.NODE_ENV as typeof process.env.NODE_ENV,
      HEALTH_CHECK_VERSION_OVERRIDE: undefined,
      HEALTH_CHECK_DISABLE_DIAGNOSTICS: undefined,
    };

    // Mock version as default
    (getApplicationVersion as jest.Mock).mockReturnValue("1.0.0");
  });

  afterAll(() => {
    // Restore original env
    process.env = originalEnv;
  });

  it("should return 200 status with correct response shape", async () => {
    // Set environment for this test
    process.env = {
      ...process.env,
      NODE_ENV: "production",
    };

    // Execute the endpoint
    const response = await GET();
    const data = await response.json();

    // Check status code
    expect(response.status).toBe(200);

    // Check response shape
    expect(data).toHaveProperty("status", "ok");
    expect(data).toHaveProperty("timestamp");
    expect(data).toHaveProperty("version", "1.0.0");
    expect(data).toHaveProperty("environment", "production");

    // Validate ISO 8601 timestamp format
    expect(Date.parse(data.timestamp)).not.toBeNaN();

    // In production, diagnostics should not be included
    expect(data).not.toHaveProperty("diagnostics");
  });

  it("should include diagnostics in non-production environments", async () => {
    // Set environment for this test
    process.env = {
      ...process.env,
      NODE_ENV: "development",
    };

    // Execute the endpoint
    const response = await GET();
    const data = await response.json();

    // Check diagnostics are included
    expect(data).toHaveProperty("diagnostics");
    expect(data.diagnostics).toHaveProperty("memoryUsage");
    expect(data.diagnostics).toHaveProperty("uptime");
    expect(data.diagnostics).toHaveProperty("nodeVersion");
  });

  it("should use version override if provided", async () => {
    // Set version override
    process.env = {
      ...process.env,
      HEALTH_CHECK_VERSION_OVERRIDE: "2.0.0",
    };

    // Execute the endpoint
    const response = await GET();
    const data = await response.json();

    // Check version is overridden
    expect(data).toHaveProperty("version", "2.0.0");
  });

  it("should not include diagnostics if disabled", async () => {
    // Set environment for this test
    process.env = {
      ...process.env,
      NODE_ENV: "development",
      HEALTH_CHECK_DISABLE_DIAGNOSTICS: "true",
    };

    // Execute the endpoint
    const response = await GET();
    const data = await response.json();

    // Check diagnostics are not included
    expect(data).not.toHaveProperty("diagnostics");
  });
});
