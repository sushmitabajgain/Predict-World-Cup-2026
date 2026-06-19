from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VenueRead(BaseModel):
    id: int
    name: str
    city: str
    country: str
    timezone: str

    model_config = ConfigDict(from_attributes=True)


class TournamentRead(BaseModel):
    id: int
    name: str
    season: str
    host_countries: list[str]
    stages: list[str]
    groups: list[str]


class MatchTeamRead(BaseModel):
    id: int
    name: str
    fifa_code: str
    flag_url: str | None = None


class MatchPredictionRead(BaseModel):
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    predicted_home_score: int
    predicted_away_score: int
    confidence: str
    explanation: str
    generated_at: datetime


class TournamentMatchRead(BaseModel):
    id: int
    stage: str
    group: str | None
    home_team: MatchTeamRead | None
    away_team: MatchTeamRead | None
    venue: VenueRead | None
    kickoff_time_utc: datetime | None
    status: str
    home_score: int | None
    away_score: int | None
    extra_time_score: str | None
    penalty_score: str | None
    winner_team: MatchTeamRead | None
    result_text: str | None
    data_quality: str
    prediction: MatchPredictionRead | None = None


class StandingRead(BaseModel):
    group: str
    team: MatchTeamRead
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    form: str


class MatchEventRead(BaseModel):
    minute: int | None
    stoppage_time: int | None
    event_type: str
    team: MatchTeamRead | None
    player_name: str | None
    assist_player_name: str | None
    card_type: str | None
    description: str | None


class MatchDetailRead(TournamentMatchRead):
    events: list[MatchEventRead]
    stats: dict[str, object] | None
    standings: list[StandingRead]
    unavailable_fields: list[str]
