import React from 'react';

function percent(value) {
  return `${Math.round(value * 100)}%`;
}

export default function PreviousPredictionsTable({ predictions }) {
  return (
    <section className="panel history-panel">
      <h2>Previous predictions</h2>
      {predictions.length === 0 ? (
        <p className="muted">No predictions stored yet.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Match</th>
                <th>Date</th>
                <th>Team A</th>
                <th>Draw</th>
                <th>Team B</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {predictions.map((item) => (
                <tr key={item.id}>
                  <td>
                    {item.team_a} vs {item.team_b}
                  </td>
                  <td>{item.match_date}</td>
                  <td>{percent(item.team_a_win_probability)}</td>
                  <td>{percent(item.draw_probability)}</td>
                  <td>{percent(item.team_b_win_probability)}</td>
                  <td>{item.confidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
