import React from 'react';

export default function StandingsTable({ standings }) {
  if (!standings.length) {
    return <p className="muted">Standings data not available yet.</p>;
  }
  return (
    <div className="table-wrap compact-table">
      <table>
        <thead>
          <tr>
            <th>Team</th>
            <th>P</th>
            <th>W</th>
            <th>D</th>
            <th>L</th>
            <th>GD</th>
            <th>Pts</th>
            <th>Form</th>
          </tr>
        </thead>
        <tbody>
          {standings.map((row) => (
            <tr key={`${row.group}-${row.team.id}`}>
              <td>{row.team.name}</td>
              <td>{row.played}</td>
              <td>{row.won}</td>
              <td>{row.drawn}</td>
              <td>{row.lost}</td>
              <td>{row.goal_difference}</td>
              <td>{row.points}</td>
              <td>{row.form}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
