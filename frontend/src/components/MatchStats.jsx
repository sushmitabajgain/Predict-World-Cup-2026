import React from 'react';

export default function MatchStats({ stats }) {
  if (!stats || (Array.isArray(stats) && stats.length === 0)) {
    return <p className="muted">Match statistics not available yet.</p>;
  }
  if (Array.isArray(stats)) {
    return (
      <div className="stats-teams">
        {stats.map((teamStats) => (
          <section className="stats-team" key={teamStats.team || 'team'}>
            <h4>{teamStats.team || 'Team'}</h4>
            <div className="stats-grid">
              {(teamStats.statistics || []).map((item) => (
                <div key={`${teamStats.team}-${item.type}`}>
                  <span>{item.type}</span>
                  <strong>{item.value ?? 'Data not available yet'}</strong>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    );
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
