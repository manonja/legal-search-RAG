// Learn more: https://github.com/testing-library/jest-dom
import "@testing-library/jest-dom";

// Mock the next/navigation router hooks
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
  }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock environment variables
process.env = {
  ...process.env,
  NEXT_PUBLIC_API_URL: "http://localhost:8000",
  NEXT_PUBLIC_API_TOKEN: "test-token",
};

// Mock window.__NEXT_DATA__ for testing the useApiToken hook
// Create a mock window if it doesn't exist (Node.js environment)
if (typeof window === "undefined") {
  global.window = {
    __NEXT_DATA__: {
      props: {
        pageProps: {},
        __N_SSG: true,
      },
      runtimeConfig: {
        apiToken: "runtime-test-token",
      },
    },
  };
} else {
  // If window exists (jsdom environment), extend it
  Object.defineProperty(window, "__NEXT_DATA__", {
    value: {
      props: {
        pageProps: {},
        __N_SSG: true,
      },
      runtimeConfig: {
        apiToken: "runtime-test-token",
      },
    },
  });
}
