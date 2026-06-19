import React from 'react';

export default function KnockoutBracket({ matches, onOpen }) {
  const stages = ['Round of 32', 'Round of 16', 'Quarter-finals', 'Semi-finals', 'Third-place match', 'Final'];
  return (
    <div className="bracket-grid">
      {stages.map((stage) => (
        <section className="bracket-column" key={stage}>
          <h3>{stage}</h3>
          {matches.filter((match) => match.stage === stage).map((match) => (
            <button className="bracket-slot" key={match.id} type="button" onClick={() => onOpen(match.id)}>
              <span>{match.home_team?.name || 'TBD'}</span>
              <span>{match.away_team?.name || 'TBD'}</span>
            </button>
          ))}
        </section>
      ))}
    </div>
  );
}
