/**
 * NetraGraph AI Client Error Logging Utility
 */
export function reportClientError(error: unknown, context: Record<string, unknown> = {}) {
  if (typeof window === "undefined") return;
  console.error("[NetraGraph Telemetry] Intercepted client error:", error, context);
}
