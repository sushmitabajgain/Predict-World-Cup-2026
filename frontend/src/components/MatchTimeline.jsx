import React from 'react';

export default function MatchTimeline({ events }) {
  if (!events.length) {
    return <p className="muted">Timeline data not available yet.</p>;
  }
  return (
    <ol className="timeline">
      {events.map((event, index) => (
        <li key={`${event.minute}-${event.event_type}-${index}`}>
          <strong>
            {event.minute ?? '-'}
            {event.stoppage_time ? `+${event.stoppage_time}` : ''}'
          </strong>
          <span>{event.event_type}</span>
          <span>{event.player_name || event.description || 'Data not available yet'}</span>
          <em>{event.team?.name}</em>
        </li>
      ))}
    </ol>
  );
}
