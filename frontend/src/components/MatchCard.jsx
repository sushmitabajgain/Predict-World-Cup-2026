import React from 'react';
import { CalendarClock, MapPin } from 'lucide-react';
import PredictionCard from './PredictionCard.jsx';

function teamName(team) {
  return team?.name || 'TBD';
}

function groupLabel(group) {
  if (!group) return null;
  return group.startsWith('Group ') ? group : `Group ${group}`;
}

function kickoffLabel(match) {
  if (!match.kickoff_time_utc) return 'Date not available yet';
  return new Date(match.kickoff_time_utc).toLocaleString();
}

function venueLabel(match) {
  if (!match.venue) return 'Venue not available yet';
  return `${match.venue.name}, ${match.venue.city}`;
}

export default function MatchCard({ match, onOpen }) {
  return (
    <article className="match-card">
      <button className="match-open" type="button" onClick={() => onOpen(match.id)}>
        <div className="match-meta">
          <span>{match.stage}</span>
          {match.group && <span>{groupLabel(match.group)}</span>}
          <span className={`status ${match.status}`}>{match.status}</span>
        </div>
        <div className="teams-line">
          <strong>
            {match.home_team?.flag_url && <img className="team-logo" src={match.home_team.flag_url} alt="" />}
            {teamName(match.home_team)}
          </strong>
          <span>{match.home_score ?? '-'}</span>
          <small>vs</small>
          <span>{match.away_score ?? '-'}</span>
          <strong>
            {match.away_team?.flag_url && <img className="team-logo" src={match.away_team.flag_url} alt="" />}
            {teamName(match.away_team)}
          </strong>
        </div>
        <div className="match-facts">
          <span>
            <CalendarClock size={15} aria-hidden="true" />
            {kickoffLabel(match)}
          </span>
          <span>
            <MapPin size={15} aria-hidden="true" />
            {venueLabel(match)}
          </span>
        </div>
        {match.result_text && <p className="result-text">{match.result_text}</p>}
        {match.elapsed_minute && <p className="muted">Elapsed: {match.elapsed_minute}'</p>}
      </button>
      <PredictionCard
        prediction={match.prediction}
        homeTeam={teamName(match.home_team)}
        awayTeam={teamName(match.away_team)}
      />
    </article>
  );
}
