/** All requests use the FastAPI origin, including deployments behind a proxy. */
export async function request(
  path,
  { method = "GET", body, timeout = 180000 } = {},
) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  const headers = { Accept: "application/json" };
  const key = sessionStorage.getItem("technova-api-key");
  if (key) headers["X-API-Key"] = key;
  if (body) headers["Content-Type"] = "application/json";
  try {
    const response = await fetch(path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      const message =
        typeof data.detail === "string"
          ? data.detail
          : `Request failed (${response.status}). Please try again.`;
      const error = new Error(message);
      error.status = response.status;
      throw error;
    }
    return await response.json();
  } catch (error) {
    if (error.name === "AbortError")
      throw new Error("This request took too long. Please try again.");
    if (error instanceof TypeError)
      throw new Error(
        "Cannot reach the workspace. Check your connection and try again.",
      );
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  status: () => request("/api/status", { timeout: 15000 }),
  query: (query) => request("/api/query", { method: "POST", body: { query } }),
  documents: (search, department) =>
    request(
      `/api/documents?${new URLSearchParams({ search, ...(department ? { department } : {}) })}`,
      { timeout: 15000 },
    ),
  document: (id) =>
    request(`/api/documents/${encodeURIComponent(id)}`, { timeout: 15000 }),
};
