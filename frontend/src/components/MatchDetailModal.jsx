import React from 'react';
import { X } from 'lucide-react';
import MatchStats from './MatchStats.jsx';
import MatchTimeline from './MatchTimeline.jsx';
import PredictionCard from './PredictionCard.jsx';
import StandingsTable from './StandingsTable.jsx';

export default function MatchDetailModal({ detail, loading, onClose }) {
  if (!detail && !loading) return null;
  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal-panel" role="dialog" aria-modal="true" aria-label="Match details">
        <button className="icon-button close-button" type="button" onClick={onClose} aria-label="Close">
          <X size={20} aria-hidden="true" />
        </button>
        {loading ? (
          <p>Loading match details...</p>
        ) : (
          <>
            <div className="modal-header">
              <p className="eyebrow">
                {detail.stage}
                {detail.group ? ` - ${detail.group}` : ''}
              </p>
              <h2>
                {detail.home_team?.name || 'TBD'} vs {detail.away_team?.name || 'TBD'}
              </h2>
              <p className="muted">{detail.data_quality}</p>
            </div>
            <div className="modal-section">
              <h3>Prediction</h3>
              <PredictionCard
                prediction={detail.prediction}
                homeTeam={detail.home_team?.name || 'TBD'}
                awayTeam={detail.away_team?.name || 'TBD'}
              />
            </div>
            <div className="modal-section">
              <h3>Timeline</h3>
              <MatchTimeline events={detail.events} />
            </div>
            <div className="modal-section">
              <h3>Stats</h3>
              <MatchStats stats={detail.stats} />
            </div>
            <div className="modal-section">
              <h3>Lineups</h3>
              {detail.lineups?.length ? (
                <div className="lineups-grid">
                  {detail.lineups.map((lineup) => (
                    <section key={lineup.team?.id || lineup.team?.name}>
                      <h4>{lineup.team?.name}</h4>
                      <p className="muted">{lineup.formation || 'Formation not available yet'}</p>
                    </section>
                  ))}
                </div>
              ) : (
                <p className="muted">Lineups not available yet.</p>
              )}
            </div>
            <div className="modal-section">
              <h3>Group standings</h3>
              <StandingsTable standings={detail.standings} />
            </div>
            {detail.unavailable_fields.length > 0 && (
              <p className="unavailable">Data not available yet: {detail.unavailable_fields.join(', ')}.</p>
            )}
          </>
        )}
      </section>
    </div>
  );
}
