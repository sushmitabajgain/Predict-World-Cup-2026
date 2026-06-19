import React from 'react';
import { Activity, Clock, Gauge } from 'lucide-react';
import ProbabilityBarChart from './ProbabilityBarChart.jsx';

function percent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

export default function PredictionResultCard({ prediction }) {
  if (!prediction) {
    return (
      <section className="panel empty-state">
        <Gauge aria-hidden="true" size={28} />
        <p>Select two teams to generate the first forecast.</p>
      </section>
    );
  }

  return (
    <section className="panel result-panel">
      <div className="result-header">
        <div>
          <p className="eyebrow">Prediction</p>
          <h2>
            {prediction.team_a} vs {prediction.team_b}
          </h2>
        </div>
        <span className={`confidence ${prediction.confidence}`}>{prediction.confidence}</span>
      </div>

      <ProbabilityBarChart prediction={prediction} />

      <div className="metrics-grid">
        <div>
          <span>Expected goals</span>
          <strong>
            {prediction.expected_goals_team_a.toFixed(2)} - {prediction.expected_goals_team_b.toFixed(2)}
          </strong>
        </div>
        <div>
          <span>Model</span>
          <strong>{prediction.model_version}</strong>
        </div>
      </div>

      <div className="scorelines">
        <div className="section-title">
          <Activity aria-hidden="true" size={18} />
          <h3>Most likely scorelines</h3>
        </div>
        <table>
          <thead>
            <tr>
              <th>Score</th>
              <th>Probability</th>
            </tr>
          </thead>
          <tbody>
            {prediction.most_likely_scorelines.map((row) => (
              <tr key={row.score}>
                <td>{row.score}</td>
                <td>{percent(row.probability)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="explanation">{prediction.explanation}</p>
      <p className="timestamp">
        <Clock aria-hidden="true" size={16} />
        {new Date(prediction.created_at).toLocaleString()}
      </p>
    </section>
  );
}
