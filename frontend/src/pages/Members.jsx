import { useEffect, useState } from "react";
import { api } from "../api.js";
import { fmtCents } from "../utils.js";
import Spinner from "../components/Spinner.jsx";
import Modal from "../components/Modal.jsx";

export default function Members() {
  const [members, setMembers] = useState([]);
  const [balances, setBalances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newName, setNewName] = useState("");
  const [editing, setEditing] = useState(null);
  const [editName, setEditName] = useState("");

  async function load() {
    try {
      const [m, b] = await Promise.all([api.listMembers(), api.getBalances()]);
      setError(null);
      setMembers(m);
      setBalances(b);
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.listMembers(), api.getBalances()])
      .then(([m, b]) => {
        if (cancelled) return;
        setError(null);
        setMembers(m);
        setBalances(b);
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

  async function addMember(e) {
    e.preventDefault();
    const name = newName.trim();
    if (!name) return;
    try {
      await api.createMember({ name });
      setNewName("");
      await load();
    } catch (err) {
      setError(String(err.message || err));
    }
  }

  async function toggleActive(member) {
    try {
      await api.updateMember(member.id, { is_active: !member.is_active });
      await load();
    } catch (err) {
      setError(String(err.message || err));
    }
  }

  async function saveEdit(e) {
    e.preventDefault();
    try {
      await api.updateMember(editing.id, { name: editName.trim() });
      setEditing(null);
      await load();
    } catch (err) {
      setError(String(err.message || err));
    }
  }

  async function remove(member) {
    if (!window.confirm(`Delete ${member.name}? This cannot be undone.`)) return;
    try {
      await api.deleteMember(member.id);
      await load();
    } catch (err) {
      setError(String(err.message || err));
    }
  }

  const balanceOf = (id) =>
    balances.find((b) => b.member_id === id)?.balance_cents ?? 0;

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Members</h1>
          <p className="muted">Who lives in the household.</p>
        </div>
      </div>

      <div className="card">
        <form className="inline-form" onSubmit={addMember}>
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="New member name…"
            aria-label="New member name"
          />
          <button className="btn primary" disabled={!newName.trim()}>
            Add member
          </button>
        </form>
      </div>

      {error && <div className="banner error">{error}</div>}

      {loading ? (
        <Spinner />
      ) : (
        <div className="card table-card">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Status</th>
                <th className="num">Balance</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {members.map((m) => {
                const b = balanceOf(m.id);
                return (
                  <tr key={m.id} className={m.is_active ? "" : "row-inactive"}>
                    <td className="strong">{m.name}</td>
                    <td>
                      {m.is_active ? (
                        <span className="chip ok">active</span>
                      ) : (
                        <span className="chip">inactive</span>
                      )}
                    </td>
                    <td className={`num ${b > 0 ? "pos" : b < 0 ? "neg" : ""}`}>
                      {b > 0 ? `+${fmtCents(b)}` : fmtCents(b)}
                    </td>
                    <td className="actions">
                      <button
                        className="btn ghost small"
                        onClick={() => {
                          setEditing(m);
                          setEditName(m.name);
                        }}
                      >
                        Rename
                      </button>
                      <button
                        className="btn ghost small"
                        onClick={() => toggleActive(m)}
                      >
                        {m.is_active ? "Deactivate" : "Activate"}
                      </button>
                      <button
                        className="btn ghost small danger"
                        onClick={() => remove(m)}
                        disabled={!m.is_active}
                        title={
                          m.is_active
                            ? "Deactivate before deleting"
                            : "Delete member"
                        }
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {editing && (
        <Modal title="Rename member" onClose={() => setEditing(null)}>
          <form className="expense-form" onSubmit={saveEdit}>
            <div className="field">
              <label htmlFor="mm-name">Name</label>
              <input
                id="mm-name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                autoFocus
              />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn ghost" onClick={() => setEditing(null)}>
                Cancel
              </button>
              <button type="submit" className="btn primary" disabled={!editName.trim()}>
                Save
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}