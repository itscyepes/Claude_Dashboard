import { useState, useEffect, useCallback } from "react";
import "./App.css";
import { getStats, getSession } from "./api";
import StatBar from "./components/StatBar";
import SessionList from "./components/SessionList";
import SessionDetail from "./components/SessionDetail";

export default function App() {
  const [stats, setStats] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedSession, setSelectedSession] = useState(null);
  const [refreshTick, setRefreshTick] = useState(0);

  const refresh = useCallback(() => setRefreshTick((n) => n + 1), []);

  // Poll stats every 5 s
  useEffect(() => {
    let alive = true;
    const load = () => getStats().then((d) => { if (alive) setStats(d); }).catch(() => {});
    load();
    const id = setInterval(load, 5000);
    return () => { alive = false; clearInterval(id); };
  }, [refreshTick]);

  // Load selected session when id or refreshTick changes
  useEffect(() => {
    if (!selectedId) { setSelectedSession(null); return; }
    getSession(selectedId)
      .then(setSelectedSession)
      .catch(() => { setSelectedId(null); setSelectedSession(null); });
  }, [selectedId, refreshTick]);

  const handleSelectSession = (id) => {
    setSelectedId(id === selectedId ? null : id);
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-dot" />
        <span className="header-title">Claude Code Operator Dashboard</span>
        <StatBar stats={stats} />
      </header>

      <div className="app-body">
        <SessionList
          selectedId={selectedId}
          onSelect={handleSelectSession}
          onRefresh={refresh}
          refreshTick={refreshTick}
        />

        {selectedSession ? (
          <SessionDetail
            session={selectedSession}
            onRefresh={refresh}
            onDelete={() => { setSelectedId(null); refresh(); }}
          />
        ) : (
          <div className="detail-panel">
            <div className="empty-state">
              <div className="empty-state-icon">⬛</div>
              <div className="empty-state-text">Select a session to inspect</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
