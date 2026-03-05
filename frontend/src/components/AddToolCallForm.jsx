import { useState } from "react";
import { createToolCall } from "../api";

const TOOL_NAMES = ["bash", "write", "edit", "read", "other"];

export default function AddToolCallForm({ sessionId, onAdded }) {
  const [toolName, setToolName] = useState("bash");
  const [command, setCommand] = useState("");
  const [outputPreview, setOutputPreview] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createToolCall({
        session_id: sessionId,
        tool_name: toolName,
        command: command.trim() || null,
        output_preview: outputPreview.trim() || null,
      });
      setCommand("");
      setOutputPreview("");
      onAdded();
    } catch (err) {
      setError(err?.response?.data?.detail ?? "Failed to add tool call");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="add-form" onSubmit={handleSubmit}>
      <div className="add-form-title">Log Tool Call</div>

      <div className="add-form-row">
        <div className="field" style={{ flexShrink: 0 }}>
          <div className="field-label">Tool</div>
          <select className="select" value={toolName} onChange={(e) => setToolName(e.target.value)}>
            {TOOL_NAMES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <div className="field" style={{ flex: 1 }}>
          <div className="field-label">Command / Input</div>
          <input
            className="input"
            placeholder='e.g. rm -rf /tmp/build'
            value={command}
            onChange={(e) => setCommand(e.target.value)}
          />
        </div>
      </div>

      <div className="field">
        <div className="field-label">Output Preview (optional)</div>
        <input
          className="input"
          placeholder="First line of output…"
          value={outputPreview}
          onChange={(e) => setOutputPreview(e.target.value)}
        />
      </div>

      {error && (
        <div style={{ color: "var(--red)", fontSize: 11 }}>{error}</div>
      )}

      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button className="btn primary" type="submit" disabled={submitting}>
          {submitting ? "Analyzing…" : "Submit & Analyze"}
        </button>
      </div>
    </form>
  );
}
