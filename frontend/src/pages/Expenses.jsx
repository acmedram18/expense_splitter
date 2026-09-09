import { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import { fmtCents, fmtDate, monthLabel, monthKey } from "../utils.js";
import Spinner from "../components/Spinner.jsx";
import Modal from "../components/Modal.jsx";
import ExpenseForm from "../components/ExpenseForm.jsx";

function splitSummary(expense, members) {
  const name = (id) => members.find((m) => m.id === id)?.name ?? "?";
  const n = expense.shares.length;
  if (expense.split_mode === "equal") return `Equal ÷ ${n}`;
  if (expense.split_mode === "percent") {
    const max = expense.shares
      .slice()
      .sort((a, b) => b.share_cents - a.share_cents)
      .slice(0, 2)
      .map((s) => `${Math.round((s.share_cents / expense.amount_cents) * 100)}%`)
      .join(" / ");
    return max;
  }
  return expense.shares
    .map((s) => `${name(s.member_id)} ${fmtCents(s.share_cents)}`)
    .join(", ");
}

export default function Expenses() {
  const [expenses, setExpenses] = useState([]);
  const [members, setMembers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({ month: "", category: "", member: "" });
  const [editing, setEditing] = useState(null);
  const [showForm, setShowForm] = useState(false);

  async function load() {
    try {
      const [e, m, c] = await Promise.all([
        api.listExpenses(),
        api.listMembers(),
        api.listCategories(),
      ]);
      setError(null);
      setExpenses(e);
      setMembers(m);
      setCategories(c);
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      api.listExpenses(),
      api.listMembers(),
      api.listCategories(),
    ])
      .then(([e, m, c]) => {
        if (cancelled) return;
        setError(null);
        setExpenses(e);
        setMembers(m);
        setCategories(c);
      })
      .catch((err) => {
        if (!cancelled) setError(String(err.message || err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const monthOptions = useMemo(() => {
    const keys = [...new Set(expenses.map((e) => monthKey(e.date)))].sort();
    return keys;
  }, [expenses]);

  const filtered = useMemo(() => {
    const memberIds = new Set(
      filters.member ? [Number(filters.member)] : []
    );
    const involved = (e) =>
      e.paid_by === Number(filters.member) ||
      e.shares.some((s) => memberIds.has(s.member_id));
    return expenses
      .filter((e) => !filters.month || monthKey(e.date) === filters.month)
      .filter(
        (e) =>
          !filters.category ||
          e.category_id === Number(filters.category)
      )
      .filter((e) => !filters.member || involved(e))
      .sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : a.id - b.id));
  }, [expenses, filters]);

  const catName = (id) => categories.find((c) => c.id === id)?.name ?? "Uncategorized";
  const memberName = (id) => members.find((m) => m.id === id)?.name ?? "?";

  async function handleDelete(expense) {
    if (!window.confirm(`Delete “${expense.description}”?`)) return;
    try {
      await api.deleteExpense(expense.id);
      await load();
    } catch (err) {
      setError(String(err.message || err));
    }
  }

  function openEdit(expense) {
    setEditing(expense);
    setShowForm(true);
  }

  function openNew() {
    setEditing(null);
    setShowForm(true);
  }

  const total = filtered.reduce((sum, e) => sum + e.amount_cents, 0);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Expenses</h1>
          <p className="muted">{filtered.length} expenses · {fmtCents(total)} total</p>
        </div>
        <button className="btn primary" onClick={openNew}>
          + Add expense
        </button>
      </div>

      <div className="filters">
        <label className="field inline">
          <span>Month</span>
          <select
            value={filters.month}
            onChange={(e) => setFilters((f) => ({ ...f, month: e.target.value }))}
          >
            <option value="">All</option>
            {monthOptions.map((k) => (
              <option key={k} value={k}>
                {monthLabel(k)}
              </option>
            ))}
          </select>
        </label>
        <label className="field inline">
          <span>Category</span>
          <select
            value={filters.category}
            onChange={(e) =>
              setFilters((f) => ({ ...f, category: e.target.value }))
            }
          >
            <option value="">All</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field inline">
          <span>Member</span>
          <select
            value={filters.member}
            onChange={(e) =>
              setFilters((f) => ({ ...f, member: e.target.value }))
            }
          >
            <option value="">Everyone</option>
            {members.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </label>
        {(filters.month || filters.category || filters.member) && (
          <button
            className="btn ghost small"
            onClick={() => setFilters({ month: "", category: "", member: "" })}
          >
            Clear
          </button>
        )}
      </div>

      {error && <div className="banner error">{error}</div>}

      {loading ? (
        <Spinner />
      ) : (
        <div className="card table-card">
          <table className="table">
            <thead>
              <tr>
                <th>Expense</th>
                <th>Date</th>
                <th>Category</th>
                <th>Paid by</th>
                <th>Split</th>
                <th className="num">Amount</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filtered.map((e) => (
                <tr key={e.id}>
                  <td>
                    <span className="expense-title">{e.description}</span>
                    {e.notes && <span className="expense-notes">{e.notes}</span>}
                  </td>
                  <td className="nowrap">{fmtDate(e.date)}</td>
                  <td>
                    <span className="chip neutral">{catName(e.category_id)}</span>
                  </td>
                  <td>{memberName(e.paid_by)}</td>
                  <td className="split-cell">{splitSummary(e, members)}</td>
                  <td className="num strong">{fmtCents(e.amount_cents)}</td>
                  <td className="actions">
                    <button className="icon-btn" onClick={() => openEdit(e)} aria-label="Edit">
                      ✎
                    </button>
                    <button
                      className="icon-btn danger"
                      onClick={() => handleDelete(e)}
                      aria-label="Delete"
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="empty">
                    No expenses match. Add your first one!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <Modal
          title={editing ? "Edit expense" : "Add expense"}
          onClose={() => setShowForm(false)}
        >
          <ExpenseForm
            expense={editing}
            onClose={() => setShowForm(false)}
            onSaved={() => {
              setShowForm(false);
              load();
            }}
          />
        </Modal>
      )}
    </div>
  );
}