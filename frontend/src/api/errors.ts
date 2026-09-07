import axios from "axios";

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError<{ detail?: unknown }>(error)) {
    return fallback;
  }

  const detail = error.response?.data?.detail;
  return typeof detail === "string" ? detail : fallback;
}
