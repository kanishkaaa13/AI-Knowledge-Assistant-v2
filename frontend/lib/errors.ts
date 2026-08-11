/** Normalize an unknown error (axios response, Error, string) into a display message. */
export function extractErrorMessage(error: unknown, fallback: string): string {
  const detail =
    (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail ??
    (error instanceof Error ? error.message : null) ??
    (typeof error === "string" ? error : null);

  if (!detail) {
    return fallback;
  }

  return typeof detail === "string" ? detail : JSON.stringify(detail);
}
