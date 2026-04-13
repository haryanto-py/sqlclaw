const BASE = "/api";

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

export const api = {
  dashboard: () => get("/dashboard/stats"),
  skills:    () => get("/skills"),
  queryLogs: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/logs/queries${qs ? "?" + qs : ""}`);
  },
  security:  () => get("/security/stats"),
  tables:    () => get("/database/tables"),
  runQuery:  (sql) => post("/database/query", { sql }),
};
