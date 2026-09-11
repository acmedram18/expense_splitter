// Single integration point with the backend.
// Every function below mirrors an endpoint from _docs/specs.md and matches the
// fetch wrapper convention expected by the pages.
//
// The base URL is `/api` by default (Vite proxies it to the FastAPI dev server)
// and can be overridden with VITE_API_BASE, e.g. for a remote deployment.

const BASE_URL = import.meta.env.VITE_API_BASE ?? "/api";

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error("No se pudo conectar con el servidor");
  }
  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      /* no response body */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined;
  return res.json();
}

export const api = {
  listMembers: () => request("/members"),
  createMember: (payload) =>
    request("/members", { method: "POST", body: JSON.stringify(payload) }),
  updateMember: (id, patch) =>
    request(`/members/${id}`, { method: "PATCH", body: JSON.stringify(patch) }),
  deleteMember: (id) => request(`/members/${id}`, { method: "DELETE" }),

  listCategories: () => request("/categories"),

  listExpenses: () => request("/expenses"),
  createExpense: (payload) =>
    request("/expenses", { method: "POST", body: JSON.stringify(payload) }),
  updateExpense: (id, payload) =>
    request(`/expenses/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteExpense: (id) => request(`/expenses/${id}`, { method: "DELETE" }),

  getBalances: () => request("/balances"),
  getSettlementPlan: () => request("/settlement-plan"),

  listPayments: () => request("/payments"),
  createPayment: (payload) =>
    request("/payments", { method: "POST", body: JSON.stringify(payload) }),
  deletePayment: (id) => request(`/payments/${id}`, { method: "DELETE" }),

  getDashboard: (month) =>
    request(`/dashboard?month=${encodeURIComponent(month)}`),
};