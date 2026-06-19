import React from 'react';
import { CalendarDays, Loader2, Swords } from 'lucide-react';

export default function MatchPredictionForm({ teams, onSubmit, loading }) {
  function handleSubmit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    onSubmit({
      team_a: form.get('team_a'),
      team_b: form.get('team_b'),
      venue_type: form.get('venue_type'),
      match_date: form.get('match_date'),
    });
  }

  const today = new Date().toISOString().slice(0, 10);

  return (
    <form className="panel prediction-form" onSubmit={handleSubmit}>
      <div className="panel-title">
        <Swords aria-hidden="true" size={20} />
        <h1>World Cup match predictor</h1>
      </div>

      <div className="form-grid">
        <label>
          Team A
          <select name="team_a" defaultValue="Brazil" required>
            {teams.map((team) => (
              <option key={team.id} value={team.name}>
                {team.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Team B
          <select name="team_b" defaultValue="Scotland" required>
            {teams.map((team) => (
              <option key={team.id} value={team.name}>
                {team.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Venue
          <select name="venue_type" defaultValue="neutral">
            <option value="neutral">Neutral</option>
            <option value="home">Team A home</option>
            <option value="away">Team A away</option>
          </select>
        </label>

        <label>
          Match date
          <span className="date-field">
            <CalendarDays aria-hidden="true" size={18} />
            <input name="match_date" type="date" defaultValue="2026-06-24" min={today} required />
          </span>
        </label>
      </div>

      <button className="primary-action" type="submit" disabled={loading || teams.length < 2}>
        {loading ? <Loader2 aria-hidden="true" className="spin" size={18} /> : <Swords aria-hidden="true" size={18} />}
        Predict
      </button>
    </form>
  );
}
