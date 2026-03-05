export default function StatBar({ stats }) {
  const s = stats ?? {};

  const cards = [
    { label: "Sessions",       value: s.total_sessions   ?? "—", cls: "indigo" },
    { label: "Active",         value: s.active_sessions  ?? "—", cls: "green"  },
    { label: "Tool Calls",     value: s.total_tool_calls ?? "—", cls: "indigo" },
    { label: "Danger",         value: s.danger_count     ?? "—", cls: "red"    },
  ];

  return (
    <div className="stat-bar">
      {cards.map((c) => (
        <div className="stat-card" key={c.label}>
          <span className="stat-label">{c.label}</span>
          <span className={`stat-value ${c.cls}`}>{c.value}</span>
        </div>
      ))}
    </div>
  );
}
