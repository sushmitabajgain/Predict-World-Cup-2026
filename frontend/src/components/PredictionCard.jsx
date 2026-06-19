import React from 'react';

function percent(value) {
  return `${Math.round((value || 0) * 100)}%`;
}

export default function PredictionCard({ prediction, homeTeam, awayTeam }) {
  if (!prediction) {
    return <p className="muted">Prediction unavailable until both teams are known.</p>;
  }
  return (
    <div className="match-prediction">
      <div className="prediction-grid">
        <span>{homeTeam}</span>
        <strong>{percent(prediction.home_win_probability)}</strong>
        <span>Draw</span>
        <strong>{percent(prediction.draw_probability)}</strong>
        <span>{awayTeam}</span>
        <strong>{percent(prediction.away_win_probability)}</strong>
      </div>
      <p>
        Predicted score: {prediction.predicted_score || `${homeTeam} ${prediction.predicted_home_score}-${prediction.predicted_away_score} ${awayTeam}`}
      </p>
      {prediction.confidence && <p>Confidence: {prediction.confidence}</p>}
      <p className="muted">{prediction.explanation}</p>
    </div>
  );
}
