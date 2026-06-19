import React from 'react';

export default function MatchStats({ stats }) {
  if (!stats) {
    return <p className="muted">Match statistics not available yet.</p>;
  }
  return (
    <div className="stats-grid">
      {Object.entries(stats).map(([key, value]) => (
        <div key={key}>
          <span>{key.replaceAll('_', ' ')}</span>
          <strong>{String(value)}</strong>
        </div>
      ))}
    </div>
  );
}
