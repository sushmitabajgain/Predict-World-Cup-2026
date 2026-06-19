import React from 'react';
import { Timer } from 'lucide-react';

export default function NextMatchCard({ match }) {
  if (!match) {
    return (
      <section className="panel next-match">
        <div className="section-title">
          <Timer size={18} aria-hidden="true" />
          <h2>Next Match</h2>
        </div>
        <p className="muted">Kickoff data not available yet. Connect a sports API to populate the live schedule.</p>
      </section>
    );
  }
  return (
    <section className="panel next-match">
      <div className="section-title">
        <Timer size={18} aria-hidden="true" />
        <h2>Next Match</h2>
      </div>
      <strong>
        {match.home_team?.name || 'TBD'} vs {match.away_team?.name || 'TBD'}
      </strong>
      <p>{new Date(match.kickoff_time_utc).toLocaleString()}</p>
      <p className="muted">{match.venue ? `${match.venue.name}, ${match.venue.city}` : 'Venue not available yet'}</p>
    </section>
  );
}
