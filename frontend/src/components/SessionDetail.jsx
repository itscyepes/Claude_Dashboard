import { updateSession, deleteSession } from "../api";
import ToolCallRow from "./ToolCallRow";
import AddToolCallForm from "./AddToolCallForm";

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

export default function SessionDetail({ session, onRefresh, onDelete }) {
  const isActive = session.status === "active";

  const markComplete = async () => {
    await updateSession(session.id, { status: "completed", ended_at: new Date().toISOString() });
    onRefresh();
  };

  const abort = async () => {
    await updateSession(session.id, { status: "aborted", ended_at: new Date().toISOString() });
    onRefresh();
  };

  const handleDelete = async () => {
    if (!confirm(`Delete session "${session.name}"? This cannot be undone.`)) return;
    await deleteSession(session.id);
    onDelete();
  };

  return (
    <div className="detail-panel">
      <div className="detail-header">
        <div>
          <div className="detail-name">
            {session.name}
            <span className={`badge ${session.status}`} style={{ marginLeft: 10 }}>
              {session.status}
            </span>
          </div>
          <div className="detail-meta">
            Started {fmtDate(session.started_at)}
            {session.ended_at ? ` · Ended ${fmtDate(session.ended_at)}` : ""}
            {" · "}
            {session.total_tokens.toLocaleString()} tokens
            {" · "}
            ${session.estimated_cost_usd.toFixed(4)}
          </div>
        </div>

        <div className="detail-actions">
          {isActive && (
            <>
              <button className="btn success" onClick={markComplete}>✓ Complete</button>
              <button className="btn danger" onClick={abort}>✕ Abort</button>
            </>
          )}
          <button className="btn danger sm" onClick={handleDelete}>Delete</button>
        </div>
      </div>

      <div className="detail-body">
        {isActive && (
          <AddToolCallForm sessionId={session.id} onAdded={onRefresh} />
        )}

        <div className="tool-calls-section">
          <div className="section-label">
            Tool Calls ({session.tool_calls?.length ?? 0})
          </div>

          {(session.tool_calls ?? []).length === 0 ? (
            <div style={{ color: "var(--text-muted)", fontSize: 12, padding: "8px 0" }}>
              No tool calls logged yet.
            </div>
          ) : (
            [...(session.tool_calls ?? [])]
              .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
              .map((tc) => (
                <ToolCallRow key={tc.id} toolCall={tc} onRefresh={onRefresh} />
              ))
          )}
        </div>
      </div>
    </div>
  );
}
