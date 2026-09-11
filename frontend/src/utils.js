export function fmtCents(cents) {
  const value = Math.round(cents || 0);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value / 100);
}

export function parseDollars(input) {
  const cleaned = String(input ?? "").replace(/[^0-9.-]/g, "");
  if (cleaned === "") return NaN;
  const n = parseFloat(cleaned);
  if (!Number.isFinite(n)) return NaN;
  return Math.round(n * 100);
}

export function fmtDate(iso) {
  if (!iso) return "";
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("es-ES", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function todayISO() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate()
  ).padStart(2, "0")}`;
}

export function monthKey(iso) {
  return iso ? iso.slice(0, 7) : "";
}

export function monthLabel(key) {
  if (!key) return "";
  const [y, m] = key.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString("es-ES", {
    month: "long",
    year: "numeric",
  });
}

export function currentMonthKey() {
  return monthKey(todayISO());
}