import React from 'react';

function percent(value) {
  return `${Math.round(value * 100)}%`;
}

export default function ProbabilityBarChart({ prediction }) {
  const rows = [
    { label: prediction.team_a, value: prediction.team_a_win_probability, className: 'a' },
    { label: 'Draw', value: prediction.draw_probability, className: 'draw' },
    { label: prediction.team_b, value: prediction.team_b_win_probability, className: 'b' },
  ];

  return (
    <div className="probability-chart" aria-label="Outcome probabilities">
      {rows.map((row) => (
        <div className="probability-row" key={row.label}>
          <div className="probability-label">
            <span>{row.label}</span>
            <strong>{percent(row.value)}</strong>
          </div>
          <div className="bar-track">
            <span className={`bar ${row.className}`} style={{ width: percent(row.value) }} />
          </div>
        </div>
      ))}
    </div>
  );
}
