// Empty base = same origin (Vite proxies /api in dev). Set VITE_API_URL for a separate API host.
const BASE = import.meta.env.VITE_API_URL || "";

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      /* keep default message */
    }
    throw new Error(message);
  }
  return res.json();
}

export const imageSrc = (url) => (url ? `${BASE}${url}` : null);

export function listItems({ type, q } = {}) {
  const params = new URLSearchParams();
  if (type && type !== "all") params.set("type", type);
  if (q) params.set("q", q);
  return request(`/api/items?${params}`);
}

export function createItem(formData) {
  return request("/api/items", { method: "POST", body: formData });
}

export function getMatches(id) {
  return request(`/api/items/${id}/matches`);
}

export function resolveItem(id, token) {
  return request(`/api/items/${id}/resolve`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
}
