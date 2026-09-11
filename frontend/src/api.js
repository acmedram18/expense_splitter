// Single integration point with the backend.
// Every function below mirrors an endpoint from _docs/specs.md.
// For now it runs against an in-memory mock persisted to localStorage.
// Swap each function for a fetch() call when the FastAPI backend exists —
// the callers (pages) do not need to change.

import { todayISO, monthKey } from "./utils.js";

const STORAGE_KEY = "expense_splitter_state_v2";

const DEFAULT_CATEGORIES = [
  { id: 1, name: "Alquiler", is_custom: false },
  { id: 2, name: "Servicios", is_custom: false },
  { id: 3, name: "Supermercado", is_custom: false },
  { id: 4, name: "Transporte", is_custom: false },
  { id: 5, name: "Entretenimiento", is_custom: false },
  { id: 6, name: "Otros", is_custom: false },
];

let db = load();

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function delay(ms = 150) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
}

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    /* corrupted storage — fall through to seed */
  }
  const seeded = seed();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(seeded));
  return seeded;
}

function nextId(list) {
  return list.reduce((max, item) => Math.max(max, item.id), 0) + 1;
}

// --- seed ---------------------------------------------------------------

function iso(y, m1, d) {
  return `${y}-${String(m1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

function offsetDate(monthOffset, day) {
  const now = new Date();
  const d = new Date(now.getFullYear(), now.getMonth() + monthOffset, 1);
  const y = d.getFullYear();
  const m = d.getMonth() + 1;
  const lastDay = new Date(y, m, 0).getDate();
  return iso(y, m, Math.min(day, lastDay));
}

function seed() {
  const members = [
    { id: 1, name: "Ana", is_active: true },
    { id: 2, name: "Luis", is_active: true },
    { id: 3, name: "Marta", is_active: true },
  ];

  const expenses = [];
  let eid = 1;
  const add = (paid_by, description, amount_cents, date, category_id, split, split_mode = "equal") => {
    expenses.push({
      id: eid++,
      description,
      amount_cents,
      paid_by,
      date,
      category_id,
      notes: "",
      split_mode,
      shares: split,
    });
  };

  const eq = (ids, amount_cents) => {
    const base = Math.floor(amount_cents / ids.length);
    let rem = amount_cents - base * ids.length;
    return ids.map((member_id) => {
      const share_cents = base + (rem > 0 ? 1 : 0);
      if (rem > 0) rem -= 1;
      return { member_id, share_cents };
    });
  };

  const rent = [1, 2, 3];
  add(1, "Alquiler", 150000, offsetDate(0, 1), 1, eq(rent, 150000));
  add(2, "Alquiler", 150000, offsetDate(-1, 1), 1, eq(rent, 150000));
  add(1, "Alquiler", 150000, offsetDate(-2, 1), 1, eq(rent, 150000));
  add(2, "Alquiler", 150000, offsetDate(-3, 1), 1, eq(rent, 150000));

  add(1, "Luz y agua", 21500, offsetDate(-1, 9), 2, eq(rent, 21500));
  add(2, "Internet", 18900, offsetDate(-3, 12), 2, eq(rent, 18900));
  add(3, "Luz y agua", 17300, offsetDate(-5, 8), 2, eq(rent, 17300));

  add(3, "Supermercado", 8400, offsetDate(0, 3), 3, eq(rent, 8400));
  add(2, "Supermercado", 6320, offsetDate(0, 4), 3, eq(rent, 6320));
  add(1, "Supermercado", 11800, offsetDate(-1, 10), 3, eq(rent, 11800));
  add(3, "Supermercado", 9100, offsetDate(-1, 18), 3, eq(rent, 9100));
  add(2, "Supermercado", 13450, offsetDate(-2, 8), 3, eq(rent, 13450));
  add(3, "Supermercado", 9800, offsetDate(-3, 15), 3, eq(rent, 9800));
  add(1, "Supermercado", 12300, offsetDate(-4, 17), 3, eq(rent, 12300));

  add(2, "Gasolina / tarjeta metro", 6800, offsetDate(-1, 12), 4, eq(rent, 6800));
  add(3, "Gasolina / tarjeta metro", 4500, offsetDate(-3, 5), 4, eq(rent, 4500));

  add(3, "Cena afuera", 23000, offsetDate(-2, 21), 5, [
    { member_id: 3, share_cents: 9200 },
    { member_id: 2, share_cents: 8050 },
    { member_id: 1, share_cents: 5750 },
  ], "percent");
  add(1, "Noche de cine", 6000, offsetDate(-4, 25), 5, eq(rent, 6000));

  add(1, "Artículos para la casa", 5400, offsetDate(-5, 20), 6, eq(rent, 5400));

  const payments = [
    { id: 1, from_member_id: 2, to_member_id: 1, amount_cents: 50000, date: offsetDate(-2, 9) },
    { id: 2, from_member_id: 3, to_member_id: 1, amount_cents: 50000, date: offsetDate(-1, 7) },
  ];

  return { members, categories: DEFAULT_CATEGORIES, expenses, payments };
}

// --- balances / settlement ---------------------------------------------

export function netBalances(state = db) {
  const bal = new Map(state.members.map((m) => [m.id, 0]));
  for (const e of state.expenses) {
    const payerShare =
      e.shares.find((s) => s.member_id === e.paid_by)?.share_cents ?? 0;
    for (const s of e.shares) {
      if (s.member_id === e.paid_by) {
        bal.set(e.paid_by, bal.get(e.paid_by) + (e.amount_cents - payerShare));
      } else {
        bal.set(s.member_id, bal.get(s.member_id) - s.share_cents);
      }
    }
  }
  for (const p of state.payments) {
    bal.set(p.from_member_id, bal.get(p.from_member_id) + p.amount_cents);
    bal.set(p.to_member_id, bal.get(p.to_member_id) - p.amount_cents);
  }
  return bal;
}

function settlementPlan(state = db) {
  const name = (id) => state.members.find((m) => m.id === id)?.name ?? "?";
  const bal = netBalances(state);
  const debtors = [...bal.entries()]
    .filter(([, v]) => v < 0)
    .map(([id, v]) => ({ id, amount: -v }))
    .sort((a, b) => b.amount - a.amount);
  const creditors = [...bal.entries()]
    .filter(([, v]) => v > 0)
    .map(([id, v]) => ({ id, amount: v }))
    .sort((a, b) => b.amount - a.amount);

  const plan = [];
  let i = 0;
  let j = 0;
  while (i < debtors.length && j < creditors.length) {
    const transfer = Math.min(debtors[i].amount, creditors[j].amount);
    if (transfer > 0) {
      plan.push({
        from_member_id: debtors[i].id,
        from_name: name(debtors[i].id),
        to_member_id: creditors[j].id,
        to_name: name(creditors[j].id),
        amount_cents: transfer,
      });
      debtors[i].amount -= transfer;
      creditors[j].amount -= transfer;
    }
    if (debtors[i].amount === 0) i += 1;
    if (creditors[j].amount === 0) j += 1;
  }
  return plan;
}

// --- endpoints ----------------------------------------------------------

export const api = {
  async listMembers() {
    await delay();
    return clone(db.members);
  },

  async createMember({ name }) {
    await delay();
    const member = { id: nextId(db.members), name: name.trim(), is_active: true };
    db.members.push(member);
    persist();
    return clone(member);
  },

  async updateMember(id, patch) {
    await delay();
    const member = db.members.find((m) => m.id === id);
    if (!member) throw new Error("Miembro no encontrado");
    if (patch.name !== undefined) member.name = patch.name;
    if (patch.is_active !== undefined) member.is_active = patch.is_active;
    persist();
    return clone(member);
  },

  async deleteMember(id) {
    await delay();
    const used =
      db.expenses.some((e) => e.paid_by === id || e.shares.some((s) => s.member_id === id)) ||
      db.payments.some((p) => p.from_member_id === id || p.to_member_id === id);
    if (used) throw new Error("El miembro está en uso en gastos o pagos");
    db.members = db.members.filter((m) => m.id !== id);
    persist();
    return { ok: true };
  },

  async listCategories() {
    await delay();
    return clone(db.categories);
  },

  async listExpenses() {
    await delay();
    return clone(db.expenses);
  },

  async createExpense(payload) {
    await delay();
    const expense = { id: nextId(db.expenses), ...payload };
    validateExpense(expense);
    db.expenses.push(expense);
    persist();
    return clone(expense);
  },

  async updateExpense(id, payload) {
    await delay();
    const index = db.expenses.findIndex((e) => e.id === id);
    if (index === -1) throw new Error("Gasto no encontrado");
    const expense = { ...db.expenses[index], ...payload, id };
    validateExpense(expense);
    db.expenses[index] = expense;
    persist();
    return clone(expense);
  },

  async deleteExpense(id) {
    await delay();
    db.expenses = db.expenses.filter((e) => e.id !== id);
    persist();
    return { ok: true };
  },

  async getBalances() {
    await delay();
    const bal = netBalances();
    return db.members.map((m) => ({
      member_id: m.id,
      name: m.name,
      is_active: m.is_active,
      balance_cents: bal.get(m.id) ?? 0,
    }));
  },

  async getSettlementPlan() {
    await delay();
    return settlementPlan();
  },

  async listPayments() {
    await delay();
    return clone(db.payments);
  },

  async createPayment({ from_member_id, to_member_id, amount_cents, date }) {
    await delay();
    if (from_member_id === to_member_id) throw new Error("No puedes pagarte a ti mismo");
    if (amount_cents <= 0) throw new Error("El monto debe ser positivo");
    const payment = {
      id: nextId(db.payments),
      from_member_id,
      to_member_id,
      amount_cents,
      date: date || todayISO(),
    };
    db.payments.push(payment);
    persist();
    return clone(payment);
  },

  async deletePayment(id) {
    await delay();
    db.payments = db.payments.filter((p) => p.id !== id);
    persist();
    return { ok: true };
  },

  async getDashboard(month) {
    await delay();
    const members = [...db.members].sort((a, b) => a.id - b.id);
    const inMonth = db.expenses.filter((e) => monthKey(e.date) === month);

    const totalMonthCents = inMonth.reduce((sum, e) => sum + e.amount_cents, 0);

    const byCategoryMonth = db.categories
      .map((c) => ({
        category_id: c.id,
        name: c.name,
        total_cents: inMonth
          .filter((e) => e.category_id === c.id)
          .reduce((sum, e) => sum + e.amount_cents, 0),
      }))
      .filter((c) => c.total_cents > 0);

    const byMemberMonth = members.map((m) => ({
      member_id: m.id,
      name: m.name,
      total_cents: inMonth
        .filter((e) => e.paid_by === m.id)
        .reduce((sum, e) => sum + e.amount_cents, 0),
    }));

    const monthlySeries = [...new Set(db.expenses.map((e) => monthKey(e.date)))]
      .sort()
      .map((key) => ({
        key,
        label: new Date(`${key}-01`).toLocaleDateString("es-ES", { month: "short" }),
        total_cents: db.expenses
          .filter((e) => monthKey(e.date) === key)
          .reduce((sum, e) => sum + e.amount_cents, 0),
      }));

    const bal = netBalances();
    const balances = members.map((m) => ({
      member_id: m.id,
      name: m.name,
      balance_cents: bal.get(m.id) ?? 0,
    }));

    return {
      month,
      totalMonthCents,
      byCategoryMonth,
      byMemberMonth,
      monthlySeries,
      balances,
      plan: settlementPlan(),
    };
  },
};

function validateExpense(expense) {
  if (!expense.description?.trim()) throw new Error("La descripción es obligatoria");
  if (!Number.isFinite(expense.amount_cents) || expense.amount_cents <= 0) {
    throw new Error("El monto debe ser mayor que cero");
  }
  const total = expense.shares.reduce((sum, s) => sum + s.share_cents, 0);
  if (total !== expense.amount_cents) {
    throw new Error("Las partes deben sumar el monto del gasto");
  }
}