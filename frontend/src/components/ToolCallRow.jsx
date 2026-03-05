import { updateToolCall } from "../api";

function fmtTs(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function ToolCallRow({ toolCall: tc, onRefresh }) {
  const needsReview = !tc.approved && (tc.risk_level === "warning" || tc.risk_level === "danger");

  const approve = async () => {
    await updateToolCall(tc.id, { approved: true });
    onRefresh();
  };

  const reject = async () => {
    await updateToolCall(tc.id, { approved: false });
    onRefresh();
  };

  return (
    <div className={`tool-call-row ${tc.risk_level}`}>
      <div className="tool-call-main">
        <div className="tool-call-top">
          <span className={`badge ${tc.tool_name}`}>{tc.tool_name}</span>
          <span className={`badge ${tc.risk_level}`}>{tc.risk_level}</span>
          <span className="tool-call-ts">{fmtTs(tc.timestamp)}</span>
        </div>

        {tc.command && (
          <div className="tool-call-command">{tc.command}</div>
        )}

        {tc.risk_reason && (
          <div className="tool-call-reason">{tc.risk_reason}</div>
        )}

        {tc.output_preview && (
          <div className="tool-call-reason" style={{ marginTop: 4, fontStyle: "italic" }}>
            ↳ {tc.output_preview}
          </div>
        )}
      </div>

      <div className="tool-call-actions">
        {tc.approved && (
          <span className="approved-badge">✓ APPROVED</span>
        )}
        {needsReview && (
          <>
            <button className="btn success sm" onClick={approve}>Approve</button>
            <button className="btn danger sm" onClick={reject}>Reject</button>
          </>
        )}
      </div>
    </div>
  );
}
