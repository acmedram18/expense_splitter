import { useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import { parseDollars, fmtCents, todayISO } from "../utils.js";

const MODES = [
  { id: "equal", label: "Igual" },
  { id: "percent", label: "Porcentaje" },
  { id: "custom", label: "Montos personalizados" },
];

function round2(v) {
  return Math.round(v * 100) / 100;
}

export default function ExpenseForm({ expense, onClose, onSaved }) {
  const [members, setMembers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState({
    description: "",
    amountStr: "",
    date: todayISO(),
    paidById: "",
    categoryId: "",
    notes: "",
    mode: "equal",
    participants: [],
    perPct: {},
    perAmt: {},
  });
  const [submitError, setSubmitError] = useState(null);
  const [saving, setSaving] = useState(false);

  function initForm(prev, m, c, existing) {
    if (!existing) {
      const active = m.filter((x) => x.is_active);
      const paidById = active[0]?.id ?? "";
      const participants = active.map((x) => x.id);
      return {
        ...prev,
        participants,
        paidById: String(paidById),
        categoryId: "",
      };
    }
    const participants = existing.shares.map((s) => s.member_id);
    const perAmt = {};
    existing.shares.forEach((s) => {
      perAmt[s.member_id] = (s.share_cents / 100).toFixed(2);
    });
    const allEqual = existing.shares.every(
      (s) => s.share_cents === existing.shares[0].share_cents
    );
    return {
      description: existing.description,
      amountStr: (existing.amount_cents / 100).toFixed(2),
      date: existing.date,
      paidById: String(existing.paid_by),
      categoryId: existing.category_id ? String(existing.category_id) : "",
      notes: existing.notes || "",
      mode: allEqual ? "equal" : "custom",
      participants,
      perPct: defaultsFor("percent", existing.shares, 0),
      perAmt,
    };
  }

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.listMembers(), api.listCategories()]).then(([m, c]) => {
      if (cancelled) return;
      setMembers(m);
      setCategories(c);
      setForm((prev) => initForm(prev, m, c, expense));
    });
    return () => {
      cancelled = true;
    };
  }, [expense]);

  const availableMembers = useMemo(() => {
    if (!members.length) return [];
    const active = members.filter((m) => m.is_active);
    const lockedIds = (expense?.shares ?? []).map((s) => s.member_id);
    const locked = members.filter((m) => !m.is_active && lockedIds.includes(m.id));
    return [...active, ...locked].sort((a, b) => a.id - b.id);
  }, [members, expense]);

  const amountCents = useMemo(() => parseDollars(form.amountStr), [form.amountStr]);
  const amountOk = Number.isFinite(amountCents) && amountCents > 0;

  const splitValidation = useMemo(() => {
    if (form.mode === "equal") return { ok: true, errors: {} };
    const errors = {};
    for (const id of form.participants) {
      const raw =
        form.mode === "percent" ? form.perPct[id] : form.perAmt[id];
      const value =
        form.mode === "percent" ? parseFloat(raw) : parseDollars(raw);
      if (raw === undefined || raw === "" || !Number.isFinite(value) || value < 0) {
        errors[id] = form.mode === "percent" ? "Se requiere un número" : "Se requiere un monto";
      }
    }
    if (form.mode === "percent") {
      const sum = form.participants.reduce(
        (acc, id) => acc + (parseFloat(form.perPct[id]) || 0),
        0
      );
      if (Math.abs(sum - 100) > 0.02) {
        errors.global = `Los porcentajes deben sumar 100 (ahora ${round2(sum)})`;
      }
    } else {
      const sum = form.participants.reduce(
        (acc, id) => acc + (parseDollars(form.perAmt[id]) || 0),
        0
      );
      if (amountOk && Math.abs(sum - amountCents) > 1) {
        errors.global = `Los montos deben sumar ${fmtCents(amountCents)} (ahora ${fmtCents(sum)})`;
      }
    }
    return { ok: Object.keys(errors).length === 0, errors };
  }, [form, amountCents, amountOk]);

  const canSave =
    form.description.trim() &&
    amountOk &&
    form.participants.length >= 2 &&
    form.paidById &&
    splitValidation.ok;

  function set(patch) {
    setForm((prev) => ({ ...prev, ...patch }));
  }

  function defaultsFor(mode, participantIds, amount) {
    const result = {};
    const n = participantIds.length || 1;
    for (const id of participantIds) {
      if (mode === "percent") {
        result[id] = round2(100 / n).toFixed(2);
      } else {
        result[id] = (amount / n / 100).toFixed(2);
      }
    }
    return result;
  }

  function toggleParticipant(id) {
    setForm((prev) => {
      const on = prev.participants.includes(id);
      const participants = on
        ? prev.participants.filter((x) => x !== id)
        : [...prev.participants, id];
      const perPct = { ...prev.perPct };
      const perAmt = { ...prev.perAmt };
      if (!on) {
        const n = participants.length;
        perPct[id] = round2(100 / n).toFixed(2);
        perAmt[id] = (amountOk ? amountCents / n / 100 : 0).toFixed(2);
      } else {
        delete perPct[id];
        delete perAmt[id];
      }
      return { ...prev, participants, perPct, perAmt };
    });
  }

  function switchMode(nextMode) {
    setForm((prev) => {
      const patch = { mode: nextMode };
      if (nextMode === "percent") {
        patch.perPct = defaultsFor("percent", prev.participants, 0);
      } else if (nextMode === "custom") {
        patch.perAmt = defaultsFor("custom", prev.participants, amountOk ? amountCents : 0);
      }
      return { ...prev, ...patch };
    });
  }

  function buildShares() {
    const participants = form.participants;
    if (form.mode === "equal") {
      const base = Math.floor(amountCents / participants.length);
      const rem = amountCents - base * participants.length;
      const payerIdx = participants.indexOf(Number(form.paidById));
      const remainderIdx = payerIdx >= 0 ? payerIdx : 0;
      return participants.map((id, i) => ({
        member_id: id,
        share_cents: base + (i === remainderIdx ? rem : 0),
      }));
    }
    if (form.mode === "percent") {
      const shares = participants.map((id) => ({
        member_id: id,
        share_cents: Math.floor(
          (amountCents * (parseFloat(form.perPct[id]) || 0)) / 100
        ),
      }));
      const diff =
        amountCents - shares.reduce((acc, s) => acc + s.share_cents, 0);
      const payerIdx = shares.findIndex(
        (s) => s.member_id === Number(form.paidById)
      );
      shares[payerIdx >= 0 ? payerIdx : 0].share_cents += diff;
      return shares;
    }
    return participants.map((id) => ({
      member_id: id,
      share_cents: parseDollars(form.perAmt[id]),
    }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!canSave) return;
    setSaving(true);
    setSubmitError(null);
    const payload = {
      description: form.description.trim(),
      amount_cents: amountCents,
      paid_by: Number(form.paidById),
      date: form.date,
      category_id: form.categoryId ? Number(form.categoryId) : null,
      notes: form.notes.trim(),
      split_mode: form.mode,
      shares: buildShares(),
    };
    try {
      if (expense) {
        await api.updateExpense(expense.id, payload);
      } else {
        await api.createExpense(payload);
      }
      onSaved();
    } catch (err) {
      setSubmitError(String(err.message || err));
    } finally {
      setSaving(false);
    }
  }

  const name = (id) => members.find((m) => m.id === id)?.name ?? "?";

  return (
    <form className="expense-form" onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="ef-description">Descripción</label>
        <input
          id="ef-description"
          value={form.description}
          onChange={(e) => set({ description: e.target.value })}
          placeholder="p. ej. Supermercado, Alquiler…"
          autoFocus
        />
      </div>

      <div className="row">
        <div className="field">
          <label htmlFor="ef-amount">Monto (USD)</label>
          <input
            id="ef-amount"
            value={form.amountStr}
            onChange={(e) => set({ amountStr: e.target.value })}
            placeholder="0.00"
            inputMode="decimal"
          />
          {form.amountStr && !amountOk && (
            <span className="field-error">Ingresa un monto válido</span>
          )}
        </div>
        <div className="field">
          <label htmlFor="ef-date">Fecha</label>
          <input
            id="ef-date"
            type="date"
            value={form.date}
            onChange={(e) => set({ date: e.target.value })}
          />
        </div>
      </div>

      <div className="row">
        <div className="field">
          <label htmlFor="ef-payer">Pagado por</label>
          <select
            id="ef-payer"
            value={form.paidById}
            onChange={(e) => set({ paidById: e.target.value })}
          >
            {members
              .filter((m) => m.is_active)
              .map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="ef-category">Categoría</label>
          <select
            id="ef-category"
            value={form.categoryId}
            onChange={(e) => set({ categoryId: e.target.value })}
          >
            <option value="">Sin categoría</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="field">
        <label>Dividir entre</label>
        <div className="chip-list">
          {availableMembers.map((m) => {
            const on = form.participants.includes(m.id);
            const locked = !m.is_active && on;
            return (
              <button
                key={m.id}
                type="button"
                className={`chip ${on ? "on" : ""}`}
                onClick={() => !locked && toggleParticipant(m.id)}
                disabled={locked}
                title={locked ? "El miembro inactivo conserva su parte" : undefined}
              >
                {m.name}
              </button>
            );
          })}
        </div>
      </div>

      <div className="field">
        <label>Modo de división</label>
        <div className="segmented">
          {MODES.map((mode) => (
            <button
              key={mode.id}
              type="button"
              className={form.mode === mode.id ? "active" : ""}
              onClick={() => switchMode(mode.id)}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>

      {form.mode === "percent" && (
        <div className="field">
          <label>Porcentajes (deben sumar 100)</label>
          <div className="split-entries">
            {form.participants.map((id) => (
              <div className="split-entry" key={id}>
                <span className="split-name">{name(id)}</span>
                <div className="split-input">
                  <input
                    value={form.perPct[id] ?? ""}
                    onChange={(e) =>
                      set({
                        perPct: { ...form.perPct, [id]: e.target.value },
                      })
                    }
                    inputMode="decimal"
                  />
                  <span>%</span>
                </div>
              </div>
            ))}
          </div>
          {splitValidation.errors.global && (
            <span className="field-error">{splitValidation.errors.global}</span>
          )}
        </div>
      )}

      {form.mode === "custom" && (
        <div className="field">
          <label>Montos por persona (deben sumar el total)</label>
          <div className="split-entries">
            {form.participants.map((id) => (
              <div className="split-entry" key={id}>
                <span className="split-name">{name(id)}</span>
                <div className="split-input">
                  <span>$</span>
                  <input
                    value={form.perAmt[id] ?? ""}
                    onChange={(e) =>
                      set({
                        perAmt: { ...form.perAmt, [id]: e.target.value },
                      })
                    }
                    inputMode="decimal"
                  />
                </div>
              </div>
            ))}
          </div>
          {splitValidation.errors.global && (
            <span className="field-error">{splitValidation.errors.global}</span>
          )}
        </div>
      )}

      {form.mode === "equal" && (
        <p className="muted">
          Cada participante paga{" "}
          {amountOk && form.participants.length > 0
            ? fmtCents(Math.floor(amountCents / form.participants.length))
            : "…"}
          {amountCents % form.participants.length !== 0 &&
            " (el sobrante lo cubre quien paga)"}
        </p>
      )}

      <div className="field">
        <label htmlFor="ef-notes">Notas (opcional)</label>
        <textarea
          id="ef-notes"
          value={form.notes}
          onChange={(e) => set({ notes: e.target.value })}
          rows={2}
        />
      </div>

      {submitError && <div className="banner error">{submitError}</div>}

      <div className="modal-actions">
        <button type="button" className="btn ghost" onClick={onClose}>
          Cancelar
        </button>
        <button
          type="submit"
          className="btn primary"
          disabled={!canSave || saving}
        >
          {saving ? "Guardando…" : expense ? "Guardar cambios" : "Agregar gasto"}
        </button>
      </div>
    </form>
  );
}