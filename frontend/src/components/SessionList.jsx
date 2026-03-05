import { useState, useEffect } from "react";
import { getSessions, createSession } from "../api";

function fmt(n) {
  if (n == null) return "—";
  if (n >= 1000) return (n / 1000).toFixed(1) + "k";
  return n;
}

export default function SessionList({ selectedId, onSelect, onRefresh, refreshTick }) {
  const [sessions, setSessions] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    getSessions().then(setSessions).catch(() => {});
  }, [refreshTick]);

  const handleCreate = async () => {
    if (!name.trim()) return;
    setCreating(true);
    try {
      await createSession({ name: name.trim(), notes: notes.trim() || null });
      setName(""); setNotes(""); setShowModal(false);
      onRefresh();
    } finally {
      setCreating(false);
    }
  };

  return (
    <>
      <aside className="session-panel">
        <div className="panel-header">
          <span className="panel-title">Sessions</span>
          <button className="btn primary sm" onClick={() => setShowModal(true)}>+ New</button>
        </div>

        <div className="session-list">
          {sessions.length === 0 && (
            <div className="session-empty">No sessions yet.<br />Create one to get started.</div>
          )}
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`session-item ${s.id === selectedId ? "selected" : ""}`}
              onClick={() => onSelect(s.id)}
            >
              <div className="session-item-name">
                <span>{s.name}</span>
                <span className={`badge ${s.status}`}>{s.status}</span>
              </div>
              <div className="session-item-meta">
                <span>{fmt(s.total_tokens)} tok</span>
                <span>${s.estimated_cost_usd?.toFixed(4)}</span>
              </div>
            </div>
          ))}
        </div>
      </aside>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-title">New Session</div>

            <div className="field">
              <div className="field-label">Name</div>
              <input
                className="input"
                placeholder="e.g. Fix auth bug"
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                autoFocus
              />
            </div>

            <div className="field">
              <div className="field-label">Notes (optional)</div>
              <input
                className="input"
                placeholder="Context about this session…"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>

            <div className="modal-actions">
              <button className="btn" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="btn primary" onClick={handleCreate} disabled={creating || !name.trim()}>
                {creating ? "Creating…" : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
