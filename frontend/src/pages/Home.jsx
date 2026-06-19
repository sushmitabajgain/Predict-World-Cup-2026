import React from 'react';
import { useEffect, useState } from 'react';
import MatchPredictionForm from '../components/MatchPredictionForm.jsx';
import PredictionResultCard from '../components/PredictionResultCard.jsx';
import PreviousPredictionsTable from '../components/PreviousPredictionsTable.jsx';
import TournamentDashboard from '../components/TournamentDashboard.jsx';
import { getPredictions, getTeams, predictMatch } from '../services/api.js';

export default function Home() {
  const [teams, setTeams] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([getTeams(), getPredictions()])
      .then(([teamRows, predictionRows]) => {
        setTeams(teamRows);
        setPredictions(predictionRows);
      })
      .catch((err) => setError(err.message))
      .finally(() => setInitializing(false));
  }, []);

  async function handlePredict(payload) {
    setError('');
    if (payload.team_a === payload.team_b) {
      setError('Team A and Team B must be different.');
      return;
    }
    setLoading(true);
    try {
      const result = await predictMatch(payload);
      setPrediction(result);
      setPredictions(await getPredictions());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      {!initializing && <TournamentDashboard teams={teams} />}

      <details className="manual-predictor">
        <summary>Manual prediction tool</summary>
        <section className="workspace">
          <div className="left-column">
            {initializing ? (
              <section className="panel empty-state">Loading teams...</section>
            ) : (
              <MatchPredictionForm teams={teams} onSubmit={handlePredict} loading={loading} />
            )}
            {error && <p className="error-banner">{error}</p>}
          </div>
          <PredictionResultCard prediction={prediction} />
        </section>
        <PreviousPredictionsTable predictions={predictions} />
      </details>
    </main>
  );
}
