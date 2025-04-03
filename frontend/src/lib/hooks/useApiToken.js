import { useEffect } from "react";

/**
 * Hook to ensure the API token is available in localStorage
 * This solves the issue with Next.js environment variables in containerized environments
 */
export function useApiToken() {
  useEffect(() => {
    // This code runs only in the browser
    if (typeof window !== "undefined") {
      console.log("useApiToken: Running in browser environment");

      // Check if we have the token in localStorage already
      const storedToken = localStorage.getItem("api_token");
      console.log("useApiToken: Stored token exists?", !!storedToken);

      // If token is not in localStorage, try to get it from window.__NEXT_DATA__
      if (!storedToken) {
        try {
          console.log("useApiToken: Attempting to retrieve token from sources");
          console.log(
            "useApiToken: NEXT_PUBLIC_API_TOKEN =",
            process.env.NEXT_PUBLIC_API_TOKEN
          );

          // This is where Next.js exposes environment variables to the client
          const nextData = window.__NEXT_DATA__;
          console.log("useApiToken: __NEXT_DATA__ available?", !!nextData);

          const runtimeConfig = nextData?.runtimeConfig || {};
          console.log(
            "useApiToken: runtimeConfig =",
            JSON.stringify(runtimeConfig)
          );

          const apiToken =
            runtimeConfig.apiToken ||
            process.env.NEXT_PUBLIC_API_TOKEN ||
            "test";
          console.log("useApiToken: Final token value =", apiToken);

          // Store the token in localStorage
          localStorage.setItem("api_token", apiToken);
          console.log("useApiToken: Token stored in localStorage");
        } catch (error) {
          console.error("Error storing API token:", error);
        }
      }
    }
  }, []);
}
