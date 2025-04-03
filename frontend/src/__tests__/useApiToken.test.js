import { useApiToken } from "@/lib/hooks/useApiToken";
import { renderHook } from "@testing-library/react";

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, "localStorage", { value: mockLocalStorage });

// Store original __NEXT_DATA__ to restore after tests
const originalNextData = window.__NEXT_DATA__;

describe("useApiToken", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReset();
    mockLocalStorage.setItem.mockReset();

    // Reset the __NEXT_DATA__ to default testing state
    if (window.__NEXT_DATA__) {
      window.__NEXT_DATA__.runtimeConfig = { apiToken: "runtime-test-token" };
    }
  });

  afterAll(() => {
    // Restore original __NEXT_DATA__ after all tests
    if (originalNextData) {
      window.__NEXT_DATA__.runtimeConfig = originalNextData.runtimeConfig;
    }
  });

  it("should not set token if it already exists in localStorage", () => {
    // Mock existing token in localStorage
    mockLocalStorage.getItem.mockReturnValue("existing-token");

    // Render the hook
    renderHook(() => useApiToken());

    // Verify localStorage.getItem was called but not setItem
    expect(mockLocalStorage.getItem).toHaveBeenCalledWith("api_token");
    expect(mockLocalStorage.setItem).not.toHaveBeenCalled();
  });

  it("should set token from runtime config if not in localStorage", () => {
    // Mock no existing token
    mockLocalStorage.getItem.mockReturnValue(null);

    // Set the runtime config token
    if (window.__NEXT_DATA__) {
      window.__NEXT_DATA__.runtimeConfig = { apiToken: "runtime-config-token" };
    }

    // Render the hook
    renderHook(() => useApiToken());

    // Verify the token was stored in localStorage
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
      "api_token",
      "runtime-config-token"
    );
  });

  it("should fall back to environment variable if runtime config is not available", () => {
    // Mock no existing token
    mockLocalStorage.getItem.mockReturnValue(null);

    // Remove runtime config token
    if (window.__NEXT_DATA__) {
      window.__NEXT_DATA__.runtimeConfig = {};
    }

    // Set env var
    const originalEnv = process.env.NEXT_PUBLIC_API_TOKEN;
    process.env.NEXT_PUBLIC_API_TOKEN = "env-var-token";

    // Render the hook
    renderHook(() => useApiToken());

    // Verify the token was stored in localStorage
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
      "api_token",
      "env-var-token"
    );

    // Clean up
    process.env.NEXT_PUBLIC_API_TOKEN = originalEnv;
  });

  it('should use default "test" value if no other sources are available', () => {
    // Mock no existing token
    mockLocalStorage.getItem.mockReturnValue(null);

    // Remove runtime config token
    if (window.__NEXT_DATA__) {
      window.__NEXT_DATA__.runtimeConfig = {};
    }

    // Remove env var
    const originalEnv = process.env.NEXT_PUBLIC_API_TOKEN;
    process.env.NEXT_PUBLIC_API_TOKEN = undefined;

    // Render the hook
    renderHook(() => useApiToken());

    // Verify default token was stored in localStorage
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith("api_token", "test");

    // Clean up
    process.env.NEXT_PUBLIC_API_TOKEN = originalEnv;
  });
});
