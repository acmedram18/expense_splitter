import { useEffect, useState } from "react";
import { api } from "../api.js";
import { fmtCents, fmtDate, todayISO, parseDollars } from "../utils.js";
import Spinner from "../components/Spinner.jsx";

export default function SettleUp() {
  const [balances, setBalances] = useState([]);
  const [plan, setPlan] = useState([]);
  const [payments, setPayments] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [manual, setManual] = useState({
    fromId: "",
    toId: "",
    amountStr: "",
    date: todayISO(),
  });

  async function load() {
    try {
      const [b, p, pay, m] = await Promise.all([
        api.getBalances(),
        api.getSettlementPlan(),
        api.listPayments(),
        api.listMembers(),
      ]);
      setError(null);
      setBalances(b);
      setPlan(p);
      setPayments(pay);
      setMembers(m);
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      api.getBalances(),
      api.getSettlementPlan(),
      api.listPayments(),
      api.listMembers(),
    ])
      .then(([b, p, pay, m]) => {
        if (cancelled) return;
        setError(null);
        setBalances(b);
        setPlan(p);
        setPayments(pay);
        setMembers(m);
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

  const name = (id) => members.find((m) => m.id === id)?.name ?? "?";

  async function markPaid(item) {
    try {
      await api.createPayment({
        from_member_id: item.from_member_id,
        to_member_id: item.to_member_id,
        amount_cents: item.amount_cents,
        date: todayISO(),
      });
      await load();
    } catch (err) {
      setError(String(err.message || err));
    }
  }

  async function recordManual(e) {
    e.preventDefault();
    const amount = parseDollars(manual.amountStr);
    if (!Number.isFinite(amount) || amount <= 0) {
      setError("Enter a valid amount");
      return;
    }
    try {
      await api.createPayment({
        from_member_id: Number(manual.fromId),
        to_member_id: Number(manual.toId),
        amount_cents: amount,
        date: manual.date,
      });
      setManual({ fromId: "", toId: "", amountStr: "", date: todayISO() });
      await load();
    } catch (err) {
      setError(String(err.message || err));
    }
  }

  async function removePayment(id) {
    try {
      await api.deletePayment(id);
      await load();
    } catch (err) {
      setError(String(err.message || err));
    }
  }

  const outstanding = balances.reduce(
    (sum, b) => sum + Math.max(0, b.balance_cents),
    0
  );

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Settle Up</h1>
          <p className="muted">
            {outstanding > 0
              ? `${fmtCents(outstanding)} to be settled`
              : "Everyone is settled up"}
          </p>
        </div>
      </div>

      {error && <div className="banner error">{error}</div>}

      {loading ? (
        <Spinner />
      ) : (
        <>
          <div className="grid two">
            <section className="card">
              <h2>Net balances</h2>
              <div className="balance-list">
                {balances.map((m) => (
                  <div key={m.member_id} className="balance-row">
                    <span className="balance-name">
                      {m.name}
                      {!m.is_active && <span className="chip">inactive</span>}
                    </span>
                    <span
                      className={`balance-amount ${
                        m.balance_cents > 0 ? "pos" : m.balance_cents < 0 ? "neg" : "zero"
                      }`}
                    >
                      {m.balance_cents > 0
                        ? `is owed ${fmtCents(m.balance_cents)}`
                        : m.balance_cents < 0
                        ? `owes ${fmtCents(-m.balance_cents)}`
                        : "settled"}
                    </span>
                  </div>
                ))}
              </div>
            </section>

            <section className="card">
              <h2>Suggested payments</h2>
              {plan.length === 0 ? (
                <p className="muted">All settled — nothing suggested.</p>
              ) : (
                <ul className="plan-list pills">
                  {plan.map((p, i) => (
                    <li key={i} className="plan-item">
                      <div className="plan-text">
                        <strong>{p.from_name}</strong> → <strong>{p.to_name}</strong>
                        <span className="plan-amount">{fmtCents(p.amount_cents)}</span>
                      </div>
                      <button className="btn primary small" onClick={() => markPaid(p)}>
                        Mark as paid
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>

          <section className="card">
            <h2>Record a payment</h2>
            <form className="settle-form" onSubmit={recordManual}>
              <label className="field inline">
                <span>Who pays</span>
                <select
                  value={manual.fromId}
                  onChange={(e) =>
                    setManual((m) => ({ ...m, fromId: e.target.value }))
                  }
                >
                  <option value="">—</option>
                  {members.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field inline">
                <span>Who receives</span>
                <select
                  value={manual.toId}
                  onChange={(e) =>
                    setManual((m) => ({ ...m, toId: e.target.value }))
                  }
                >
                  <option value="">—</option>
                  {members.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field inline">
                <span>Amount</span>
                <input
                  value={manual.amountStr}
                  onChange={(e) =>
                    setManual((m) => ({ ...m, amountStr: e.target.value }))
                  }
                  placeholder="0.00"
                  inputMode="decimal"
                />
              </label>
              <label className="field inline">
                <span>Date</span>
                <input
                  type="date"
                  value={manual.date}
                  onChange={(e) =>
                    setManual((m) => ({ ...m, date: e.target.value }))
                  }
                />
              </label>
              <button
                className="btn primary"
                disabled={
                  !manual.fromId ||
                  !manual.toId ||
                  manual.fromId === manual.toId ||
                  !parseDollars(manual.amountStr)
                }
              >
                Record
              </button>
            </form>
          </section>

          <section className="card">
            <h2>Recorded payments</h2>
            {payments.length === 0 ? (
              <p className="muted">No payments recorded yet.</p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>From</th>
                    <th>To</th>
                    <th className="num">Amount</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {payments
                    .slice()
                    .sort((a, b) => (a.date < b.date ? 1 : -1))
                    .map((p) => (
                      <tr key={p.id}>
                        <td className="nowrap">{fmtDate(p.date)}</td>
                        <td>{name(p.from_member_id)}</td>
                        <td>{name(p.to_member_id)}</td>
                        <td className="num strong">{fmtCents(p.amount_cents)}</td>
                        <td className="actions">
                          <button
                            className="icon-btn danger"
                            onClick={() => removePayment(p.id)}
                            aria-label="Delete payment"
                          >
                            ✕
                          </button>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            )}
          </section>
        </>
      )}
    </div>
  );
}