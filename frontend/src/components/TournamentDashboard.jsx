import React, { useEffect, useMemo, useState } from 'react';
import GroupSelector from './GroupSelector.jsx';
import KnockoutBracket from './KnockoutBracket.jsx';
import MatchCard from './MatchCard.jsx';
import MatchDetailModal from './MatchDetailModal.jsx';
import NextMatchCard from './NextMatchCard.jsx';
import StageTabs from './StageTabs.jsx';
import StandingsTable from './StandingsTable.jsx';
import { getMatchDetail, getMatches, getNextMatch, getStandings, getTournament } from '../services/api.js';

export default function TournamentDashboard({ teams }) {
  const [tournament, setTournament] = useState(null);
  const [matches, setMatches] = useState([]);
  const [nextMatch, setNextMatch] = useState(null);
  const [standings, setStandings] = useState([]);
  const [stage, setStage] = useState('Group Stage');
  const [group, setGroup] = useState('');
  const [team, setTeam] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    Promise.all([getTournament(), getNextMatch()])
      .then(([tournamentRow, next]) => {
        setTournament(tournamentRow);
        setNextMatch(next);
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getMatches({ stage, group, team, status }),
      getStandings(group),
    ])
      .then(([matchRows, standingRows]) => {
        setMatches(matchRows);
        setStandings(standingRows);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [stage, group, team, status]);

  const stages = tournament?.stages || ['Group Stage'];
  const groups = tournament?.groups || [];
  const isGroupStage = stage === 'Group Stage';
  const knockoutMatches = useMemo(() => matches.filter((match) => match.stage !== 'Group Stage'), [matches]);

  async function openDetail(id) {
    setDetailLoading(true);
    setDetail(null);
    try {
      setDetail(await getMatchDetail(id));
    } catch (err) {
      setError(err.message);
    } finally {
      setDetailLoading(false);
    }
  }

  return (
    <section className="dashboard">
      <div className="dashboard-header">
        <div>
          <p className="eyebrow">FIFA World Cup 2026</p>
          <h1>Match center</h1>
        </div>
        <p className="muted">Predictions are estimates. Live events require a configured football data API.</p>
      </div>

      <NextMatchCard match={nextMatch} />

      <section className="panel controls-panel">
        <StageTabs stages={stages} activeStage={stage} onChange={(value) => {
          setStage(value);
          if (value !== 'Group Stage') setGroup('');
        }} />
        {isGroupStage && <GroupSelector groups={groups} activeGroup={group} onChange={setGroup} />}
        <div className="filter-row">
          <label>
            Team
            <select value={team} onChange={(event) => setTeam(event.target.value)}>
              <option value="">All teams</option>
              {teams.map((item) => (
                <option key={item.id} value={item.name}>{item.name}</option>
              ))}
            </select>
          </label>
          <label>
            Status
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="">All statuses</option>
              <option value="scheduled">Scheduled</option>
              <option value="live">Live</option>
              <option value="halftime">Halftime</option>
              <option value="finished">Finished</option>
              <option value="postponed">Postponed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </label>
        </div>
      </section>

      {error && <p className="error-banner">{error}</p>}

      <div className="dashboard-grid">
        <section className="matches-column">
          {loading ? (
            <section className="panel empty-state">Loading matches...</section>
          ) : matches.length === 0 ? (
            <section className="panel empty-state">Data not available yet.</section>
          ) : stage === 'Group Stage' ? (
            matches.map((match) => <MatchCard key={match.id} match={match} onOpen={openDetail} />)
          ) : (
            <KnockoutBracket matches={knockoutMatches} onOpen={openDetail} />
          )}
        </section>
        <section className="panel standings-panel">
          <h2>Standings</h2>
          <StandingsTable standings={standings} />
        </section>
      </div>

      <MatchDetailModal detail={detail} loading={detailLoading} onClose={() => setDetail(null)} />
    </section>
  );
}
