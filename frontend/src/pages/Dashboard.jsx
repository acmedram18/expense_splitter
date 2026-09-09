import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { api } from "../api.js";
import { fmtCents, monthLabel, currentMonthKey } from "../utils.js";
import Spinner from "../components/Spinner.jsx";

const POSITIVE = "#2f9e44";
const NEGATIVE = "#e03131";
const NEUTRAL = "#868e96";

const PALETTE = [
  "#4c6ef5",
  "#f59f00",
  "#2f9e44",
  "#ae3ec9",
  "#f06595",
  "#15aabf",
  "#e8590c",
];

function SummaryCard({ label, value, tone }) {
  return (
    <div className={`summary-card ${tone ? `tone-${tone}` : ""}`}>
      <span className="summary-label">{label}</span>
      <span className="summary-value">{value}</span>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [month, setMonth] = useState(currentMonthKey());
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getDashboard(month)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        if (!cancelled) setError(String(e.message || e));
      });
    return () => {
      cancelled = true;
    };
  }, [month]);

  const monthOptions = useMemo(() => {
    const keys = new Set();
    (data?.monthlySeries ?? []).forEach((m) => keys.add(m.key));
    return [...keys].sort();
  }, [data]);

  if (error) {
    return <div className="banner error">Failed to load dashboard: {error}</div>;
  }
  if (!data) return <Spinner />;

  const outstanding = data.balances.reduce(
    (sum, b) => sum + Math.max(0, b.balance_cents),
    0
  );
  const activeMembers = data.balances.filter(
    (b) => Math.abs(b.balance_cents) > 0
  );
  const spendingThisMonth = data.byMemberMonth.reduce(
    (sum, m) => sum + m.total_cents,
    0
  );

  const byCategory = data.byCategoryMonth
    .map((c) => ({ name: c.name, total: c.total_cents }))
    .sort((a, b) => b.total - a.total);

  const balancePie = activeMembers
    .filter((m) => m.balance_cents !== 0)
    .map((m) => ({
      name: m.name,
      value: Math.abs(m.balance_cents),
      sign: m.balance_cents > 0 ? "+" : "-",
      owes: m.balance_cents < 0,
    }));

  const byMember = data.byMemberMonth.map((m) => ({
    name: m.name,
    total: m.total_cents,
    fill: m.total_cents > 0 ? POSITIVE : NEUTRAL,
  }));

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Dashboard</h1>
          <p className="muted">Quién debe a quién y cuánto estamos gastando.</p>
        </div>
        <div className="head-actions">
          <label className="field inline">
            <span>Month</span>
            <select value={month} onChange={(e) => setMonth(e.target.value)}>
              {monthOptions.map((k) => (
                <option key={k} value={k}>
                  {monthLabel(k)}
                </option>
              ))}
            </select>
          </label>
          <Link className="btn primary" to="/expenses">
            + Add expense
          </Link>
        </div>
      </div>

      <div className="summary-grid">
        <SummaryCard
          label={`Spent in ${monthLabel(month)}`}
          value={fmtCents(data.totalMonthCents)}
        />
        <SummaryCard
          label="Total spending this month"
          value={fmtCents(spendingThisMonth)}
        />
        <SummaryCard
          label="Outstanding balance"
          value={fmtCents(outstanding)}
          tone="blue"
        />
      </div>

      <div className="grid two">
        <section className="card">
          <h2>Net balances</h2>
          <div className="balance-list">
            {data.balances.map((m) => {
              const cls =
                m.balance_cents > 0
                  ? "pos"
                  : m.balance_cents < 0
                  ? "neg"
                  : "zero";
              return (
                <div key={m.member_id} className="balance-row">
                  <span className="balance-name">
                    {m.name}
                    {!m.is_active && <span className="chip">inactive</span>}
                  </span>
                  <span className={`balance-amount ${cls}`}>
                    {m.balance_cents > 0
                      ? `is owed ${fmtCents(m.balance_cents)}`
                      : m.balance_cents < 0
                      ? `owes ${fmtCents(-m.balance_cents)}`
                      : "settled"}
                  </span>
                </div>
              );
            })}
          </div>
        </section>

        <section className="card">
          <h2>Who owes whom</h2>
          {data.plan.length === 0 ? (
            <p className="muted">Everyone is settled up. 🎉</p>
          ) : (
            <ul className="plan-list">
              {data.plan.map((p, i) => (
                <li key={i}>
                  <strong>{p.from_name}</strong> pays{" "}
                  <strong>{p.to_name}</strong>
                  <span className="plan-amount">{fmtCents(p.amount_cents)}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <div className="grid two">
        <section className="card">
          <h2>Spending by category · {monthLabel(month)}</h2>
          <div className="chart">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={byCategory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e9ecef" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={(v) => fmtCents(v)} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => fmtCents(v)} />
                <Bar dataKey="total" radius={[4, 4, 0, 0]}>
                  {byCategory.map((_, i) => (
                    <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="card">
          <h2>Spending over time</h2>
          <div className="chart">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={data.monthlySeries}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e9ecef" />
                <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={(v) => fmtCents(v)} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(v) => fmtCents(v)}
                  labelFormatter={(label) => `Month: ${label}`}
                />
                <Line
                  type="monotone"
                  dataKey="total_cents"
                  stroke="#4c6ef5"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      <div className="grid two">
        <section className="card">
          <h2>Balance distribution</h2>
          <div className="chart">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={balancePie}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={2}
                  label
                >
                  {balancePie.map((entry, i) => (
                    <Cell
                      key={i}
                      fill={entry.owes ? NEGATIVE : POSITIVE}
                    />
                  ))}
                </Pie>
                <Tooltip formatter={(v, n) => [fmtCents(v), n]} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="card">
          <h2>Paid by member · {monthLabel(month)}</h2>
          <div className="chart">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={byMember}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e9ecef" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={(v) => fmtCents(v)} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => fmtCents(v)} />
                <Bar dataKey="total" radius={[4, 4, 0, 0]}>
                  {byMember.map((m, i) => (
                    <Cell key={i} fill={m.total > 0 ? PALETTE[i % PALETTE.length] : NEUTRAL} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>
    </div>
  );
}