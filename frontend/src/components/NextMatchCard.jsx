import React from 'react';
import { Timer } from 'lucide-react';

function countdown(kickoff) {
  if (!kickoff) return 'Kickoff time not available yet';
  const diff = new Date(kickoff).getTime() - Date.now();
  if (diff <= 0) return 'Kickoff time reached';
  const totalMinutes = Math.floor(diff / 60000);
  const days = Math.floor(totalMinutes / 1440);
  const hours = Math.floor((totalMinutes % 1440) / 60);
  const minutes = totalMinutes % 60;
  if (days > 0) return `${days}d ${hours}h ${minutes}m`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

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
      <p className="countdown">{countdown(match.kickoff_time_utc)}</p>
      <p className="muted">{match.venue ? `${match.venue.name}, ${match.venue.city}` : 'Venue not available yet'}</p>
      {match.prediction && (
        <p className="muted">
          Prediction: {Math.round(match.prediction.home_win_probability * 100)}% home,
          {' '}{Math.round(match.prediction.draw_probability * 100)}% draw,
          {' '}{Math.round(match.prediction.away_win_probability * 100)}% away
        </p>
      )}
    </section>
  );
}
