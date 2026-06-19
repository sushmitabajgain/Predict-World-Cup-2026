const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WORLD_CUP_STAGES = [
  'Group Stage',
  'Round of 32',
  'Round of 16',
  'Quarter-finals',
  'Semi-finals',
  'Third-place match',
  'Final',
];
const WORLD_CUP_GROUPS = [
  'Group A',
  'Group B',
  'Group C',
  'Group D',
  'Group E',
  'Group F',
  'Group G',
  'Group H',
  'Group I',
  'Group J',
  'Group K',
  'Group L',
];

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with ${response.status}`);
  }
  return response.json();
}

export function getTeams() {
  return request('/teams');
}

export function predictMatch(payload) {
  return request('/predict', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getPredictions() {
  return request('/predictions');
}

export function getTournament() {
  return Promise.resolve({
    id: 1,
    name: 'FIFA World Cup 2026',
    season: '2026',
    host_countries: ['Canada', 'Mexico', 'United States'],
    stages: WORLD_CUP_STAGES,
    groups: WORLD_CUP_GROUPS,
  });
}

export function getMatches(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const query = params.toString();
  return request(`/api/worldcup/matches${query ? `?${query}` : ''}`).then((rows) => rows.map(normalizeMatch));
}

export function getNextMatch() {
  return request('/api/worldcup/next-match').then((row) => (row ? normalizeMatch(row) : null));
}

export function getMatchDetail(id) {
  return request(`/api/worldcup/match/${id}`).then(normalizeDetail);
}

export function getStandings(group) {
  return request('/api/worldcup/standings').then((rows) => rows
    .filter((row) => !group || row.group === group)
    .map(normalizeStanding));
}

export function getLiveMatches() {
  return request('/api/worldcup/live').then((rows) => rows.map(normalizeMatch));
}

export function getFixturePrediction(fixtureId) {
  return request(`/api/worldcup/prediction/${fixtureId}`).then(normalizePrediction);
}

function normalizeMatch(row) {
  return {
    id: row.fixtureId,
    fixture_id: row.fixtureId,
    stage: row.stage || 'Data not available yet',
    group: row.group || null,
    home_team: normalizeTeam(row.homeTeam, row.homeLogo),
    away_team: normalizeTeam(row.awayTeam, row.awayLogo),
    venue: row.venue && row.venue !== 'Data not available yet'
      ? { id: row.fixtureId, name: row.venue, city: row.city || '', country: row.country || '', timezone: 'UTC' }
      : null,
    kickoff_time_utc: row.kickoffTimeUtc || null,
    status: row.status || 'Data not available yet',
    status_long: row.statusLong || null,
    home_score: row.homeScore,
    away_score: row.awayScore,
    winner_team: row.winner ? normalizeTeam(row.winner, null) : null,
    elapsed_minute: row.elapsedMinute,
    result_text: row.resultText || null,
    data_quality: row.dataQuality || 'Data not available yet',
    prediction: row.prediction ? normalizePrediction(row.prediction) : null,
  };
}

function normalizeDetail(row) {
  return {
    ...normalizeMatch(row),
    events: (row.timeline || []).map((event) => ({
      minute: event.minute,
      stoppage_time: event.extraMinute,
      event_type: event.type,
      team: event.team ? normalizeTeam(event.team, null) : null,
      player_name: event.player,
      assist_player_name: event.assist,
      card_type: event.cardType,
      description: event.detail,
    })),
    stats: row.statistics || null,
    lineups: row.lineups || [],
    standings: (row.standings || []).map(normalizeStanding),
    unavailable_fields: row.unavailableFields || [],
  };
}

function normalizeTeam(name, logo) {
  if (!name || name === 'Data not available yet') return null;
  return {
    id: name,
    name,
    fifa_code: name.slice(0, 3).toUpperCase(),
    flag_url: logo || null,
  };
}

function normalizeStanding(row) {
  return {
    group: row.group,
    team: normalizeTeam(row.team, row.teamLogo) || { id: row.team, name: row.team, fifa_code: 'TBD', flag_url: row.teamLogo || null },
    played: row.played,
    won: row.won,
    drawn: row.drawn,
    lost: row.lost,
    goals_for: row.goalsFor,
    goals_against: row.goalsAgainst,
    goal_difference: row.goalDifference,
    points: row.points,
    rank: row.rank,
    form: row.form || '-',
  };
}

function normalizePrediction(row) {
  const score = parseScore(row.predictedScore);
  return {
    home_win_probability: toUnit(row.homeWinProbability),
    draw_probability: toUnit(row.drawProbability),
    away_win_probability: toUnit(row.awayWinProbability),
    predicted_home_score: score.home,
    predicted_away_score: score.away,
    predicted_score: row.predictedScore,
    confidence: row.confidence,
    explanation: row.explanation,
    source: row.source,
  };
}

function toUnit(value) {
  if (value == null) return 0;
  return value > 1 ? value / 100 : value;
}

function parseScore(value) {
  const match = String(value || '').match(/(\d+)-(\d+)/);
  return {
    home: match ? Number(match[1]) : 0,
    away: match ? Number(match[2]) : 0,
  };
}
