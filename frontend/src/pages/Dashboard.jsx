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
import { useTheme } from "../theme.js";
import Spinner from "../components/Spinner.jsx";

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
  const [theme] = useTheme();
  const dark = theme === "dark";

  const gridStroke = dark ? "#2b313d" : "#e9ecef";
  const axisFill = dark ? "#9aa3b2" : "#868e96";
  const cursorFill = dark ? "#262a33" : "#f4f6fb";
  const tooltipStyle = {
    backgroundColor: dark ? "#1d2027" : "#ffffff",
    border: `1px solid ${dark ? "#2c303b" : "#e3e8ef"}`,
    borderRadius: 8,
    fontSize: 13,
  };
  const tooltipLabel = { color: dark ? "#e6e9ef" : "#1f2430" };
  const tooltipItem = { color: dark ? "#e6e9ef" : "#1f2430" };

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
    return <div className="banner error">No se pudo cargar el resumen: {error}</div>;
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
    .map((m, i) => ({
      name: m.name,
      value: Math.abs(m.balance_cents),
      fill: PALETTE[i % PALETTE.length],
    }));

  const byMember = data.byMemberMonth.map((m) => ({
    name: m.name,
    total: m.total_cents,
  }));

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Resumen</h1>
          <p className="muted">Quién debe a quién y cuánto estamos gastando.</p>
        </div>
        <div className="head-actions">
          <label className="field inline">
            <span>Mes</span>
            <select value={month} onChange={(e) => setMonth(e.target.value)}>
              {monthOptions.map((k) => (
                <option key={k} value={k}>
                  {monthLabel(k)}
                </option>
              ))}
            </select>
          </label>
          <Link className="btn primary" to="/expenses">
            + Agregar gasto
          </Link>
        </div>
      </div>

      <div className="summary-grid">
        <SummaryCard
          label={`Gastado en ${monthLabel(month)}`}
          value={fmtCents(data.totalMonthCents)}
        />
        <SummaryCard
          label="Total gastado este mes"
          value={fmtCents(spendingThisMonth)}
        />
        <SummaryCard
          label="Saldo pendiente"
          value={fmtCents(outstanding)}
          tone="blue"
        />
      </div>

      <div className="grid two">
        <section className="card">
          <h2>Balances netos</h2>
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
                    {!m.is_active && <span className="chip">inactivo</span>}
                  </span>
                  <span className={`balance-amount ${cls}`}>
                    {m.balance_cents > 0
                      ? `le deben ${fmtCents(m.balance_cents)}`
                      : m.balance_cents < 0
                      ? `debe ${fmtCents(-m.balance_cents)}`
                      : "saldado"}
                  </span>
                </div>
              );
            })}
          </div>
        </section>

        <section className="card">
          <h2>Quién le debe a quién</h2>
          {data.plan.length === 0 ? (
            <p className="muted">Todos están saldados.</p>
          ) : (
            <ul className="plan-list">
              {data.plan.map((p, i) => (
                <li key={i}>
                  <strong>{p.from_name}</strong> paga{" "}
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
          <h2>Gasto por categoría · {monthLabel(month)}</h2>
          <div className="chart">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={byCategory}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: axisFill }} />
                <YAxis
                  tickFormatter={(v) => fmtCents(v)}
                  tick={{ fontSize: 11, fill: axisFill }}
                />
                <Tooltip
                  formatter={(v) => fmtCents(v)}
                  contentStyle={tooltipStyle}
                  labelStyle={tooltipLabel}
                  itemStyle={tooltipItem}
                  cursor={{ fill: cursorFill }}
                />
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
          <h2>Gasto a lo largo del tiempo</h2>
          <div className="chart">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={data.monthlySeries}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                <XAxis dataKey="label" tick={{ fontSize: 12, fill: axisFill }} />
                <YAxis
                  tickFormatter={(v) => fmtCents(v)}
                  tick={{ fontSize: 11, fill: axisFill }}
                />
                <Tooltip
                  formatter={(v) => fmtCents(v)}
                  labelFormatter={(label) => `Mes: ${label}`}
                  contentStyle={tooltipStyle}
                  labelStyle={tooltipLabel}
                  itemStyle={tooltipItem}
                  cursor={{ stroke: gridStroke, strokeWidth: 1.5 }}
                />
                <Line
                  type="monotone"
                  dataKey="total_cents"
                  stroke={PALETTE[0]}
                  strokeWidth={2}
                  dot={{ r: 3, fill: PALETTE[0] }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      <div className="grid two">
        <section className="card">
          <h2>Distribución de balances</h2>
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
                  label={{ fill: axisFill, fontSize: 12 }}
                >
                  {balancePie.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v, n) => [fmtCents(v), n]}
                  contentStyle={tooltipStyle}
                  labelStyle={tooltipLabel}
                  itemStyle={tooltipItem}
                />
                <Legend wrapperStyle={{ color: axisFill }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="card">
          <h2>Pagado por miembro · {monthLabel(month)}</h2>
          <div className="chart">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={byMember}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: axisFill }} />
                <YAxis
                  tickFormatter={(v) => fmtCents(v)}
                  tick={{ fontSize: 11, fill: axisFill }}
                />
                <Tooltip
                  formatter={(v) => fmtCents(v)}
                  contentStyle={tooltipStyle}
                  labelStyle={tooltipLabel}
                  itemStyle={tooltipItem}
                  cursor={{ fill: cursorFill }}
                />
                <Bar dataKey="total" radius={[4, 4, 0, 0]}>
                  {byMember.map((m, i) => (
                    <Cell
                      key={i}
                      fill={m.total > 0 ? PALETTE[i % PALETTE.length] : axisFill}
                    />
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