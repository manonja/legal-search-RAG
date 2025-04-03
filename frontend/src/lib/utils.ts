import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combines multiple class names with Tailwind CSS support
 * This allows for conditional class names and proper merging of Tailwind classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Constructs the API URL based on the environment variable
 * Handles different formats that can come from Render.com and other environments
 */
export const constructApiUrl = (): string => {
  const apiUrlFromEnv = process.env.NEXT_PUBLIC_API_URL;

  console.log("API URL from env:", apiUrlFromEnv);

  if (!apiUrlFromEnv) {
    // Fallback for local development
    console.log("No API URL found, using fallback");
    return "http://localhost:8000";
  }

  // If the URL already has a protocol (http:// or https://)
  if (
    apiUrlFromEnv.startsWith("http://") ||
    apiUrlFromEnv.startsWith("https://")
  ) {
    console.log("Using API URL with protocol:", apiUrlFromEnv);
    return apiUrlFromEnv;
  }

  // For Render.com deployment where we get just the host
  // Use HTTPS for production environments
  const url = `https://${apiUrlFromEnv}`;
  console.log("Using API URL with added HTTPS protocol:", url);
  return url;
};
