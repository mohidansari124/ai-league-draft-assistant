import type { Analysis, Catalog, Draft } from "./types";
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...options,
      signal: AbortSignal.timeout(45000),
    });
  } catch {
    throw new Error(
      "Could not reach the API. Check that the backend is running on port 8000, then try again.",
    );
  }
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const detail = data?.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail
              .map((d: { msg: string }) => d.msg.replace("Value error, ", ""))
              .join(" ")
          : "The request could not be completed. Please try again.",
    );
  }
  return response.json() as Promise<T>;
}
export const getChampions = () => request<Catalog>("/api/champions");
export const analyzeDraft = (draft: Draft) =>
  request<Analysis>("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(draft),
  });
