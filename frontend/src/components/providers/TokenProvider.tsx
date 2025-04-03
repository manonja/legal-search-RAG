"use client";

import { useApiToken } from "@/lib/hooks/useApiToken";

export default function TokenProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  // Initialize the API token
  useApiToken();

  return <>{children}</>;
}
