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

// Mock global objects that might not exist in Node environment
global.Request = class Request {};
global.Headers = class Headers {
  constructor(init) {
    this.headers = new Map();
    if (init) {
      Object.entries(init).forEach(([key, value]) => {
        this.set(key, value);
      });
    }
  }

  get(name) {
    return this.headers.get(name);
  }

  set(name, value) {
    this.headers.set(name, value);
  }

  has(name) {
    return this.headers.has(name);
  }
};

// Mock URL if needed
if (typeof URL === 'undefined') {
  global.URL = require('url').URL;
}

// Mock localStorage
class LocalStorageMock {
  constructor() {
    this.store = {};
  }

  getItem(key) {
    return this.store[key] || null;
  }

  setItem(key, value) {
    this.store[key] = String(value);
  }

  removeItem(key) {
    delete this.store[key];
  }

  clear() {
    this.store = {};
  }

  key(index) {
    return Object.keys(this.store)[index] || null;
  }

  get length() {
    return Object.keys(this.store).length;
  }
}

if (typeof localStorage === 'undefined') {
  global.localStorage = new LocalStorageMock();
}

// Mock FormData
if (typeof FormData === 'undefined') {
  global.FormData = require('form-data');
}

// Set up fetch mock
global.fetch = jest.fn();

// Polyfill Response from node-fetch
if (typeof Response === 'undefined') {
  const { Response } = require('node-fetch');
  global.Response = Response;
}

// Polyfill ReadableStream for Node.js test environment
if (typeof ReadableStream === 'undefined') {
  const { ReadableStream } = require('node:stream/web');
  global.ReadableStream = ReadableStream;
}
