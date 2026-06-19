from datetime import datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

JsonType = JSON().with_variant(JSONB, "postgresql")


class Base(DeclarativeBase):
    pass


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    fifa_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    confederation: Mapped[str] = mapped_column(String(32), nullable=False)

    ratings: Mapped[list["TeamRating"]] = relationship(back_populates="team")


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    season: Mapped[str] = mapped_column(String(32), nullable=False)
    host_countries: Mapped[list[str]] = mapped_column(JsonType, nullable=False)


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    country: Mapped[str] = mapped_column(String(120), nullable=False)
    timezone: Mapped[str] = mapped_column(String(80), nullable=False)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    team_a_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    team_b_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    score_a: Mapped[int] = mapped_column(Integer, nullable=False)
    score_b: Mapped[int] = mapped_column(Integer, nullable=False)
    competition: Mapped[str] = mapped_column(String(120), nullable=False)
    venue: Mapped[str] = mapped_column(String(120), nullable=False)
    venue_type: Mapped[str] = mapped_column(String(24), nullable=False, default="neutral")
    is_neutral: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class TournamentMatch(Base):
    __tablename__ = "tournament_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"), nullable=False, index=True)
    api_match_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    stage: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    group: Mapped[str | None] = mapped_column(String(16), index=True)
    home_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    venue_id: Mapped[int | None] = mapped_column(ForeignKey("venues.id"))
    kickoff_time_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="scheduled", index=True)
    home_score: Mapped[int | None] = mapped_column(Integer)
    away_score: Mapped[int | None] = mapped_column(Integer)
    extra_time_score: Mapped[str | None] = mapped_column(String(32))
    penalty_score: Mapped[str | None] = mapped_column(String(32))
    winner_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="manual")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tournament: Mapped[Tournament] = relationship()
    home_team: Mapped[Team | None] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped[Team | None] = relationship(foreign_keys=[away_team_id])
    winner_team: Mapped[Team | None] = relationship(foreign_keys=[winner_team_id])
    venue: Mapped[Venue | None] = relationship()


class MatchEvent(Base):
    __tablename__ = "match_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("tournament_matches.id"), nullable=False, index=True)
    minute: Mapped[int | None] = mapped_column(Integer)
    stoppage_time: Mapped[int | None] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    player_id: Mapped[str | None] = mapped_column(String(120))
    player_name: Mapped[str | None] = mapped_column(String(160))
    assist_player_id: Mapped[str | None] = mapped_column(String(120))
    assist_player_name: Mapped[str | None] = mapped_column(String(160))
    card_type: Mapped[str | None] = mapped_column(String(40))
    description: Mapped[str | None] = mapped_column(Text)

    match: Mapped[TournamentMatch] = relationship()
    team: Mapped[Team | None] = relationship()


class MatchStatsSnapshot(Base):
    __tablename__ = "match_stats_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("tournament_matches.id"), nullable=False, unique=True)
    stats: Mapped[dict[str, object]] = mapped_column(JsonType, nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="sports-api")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    match: Mapped[TournamentMatch] = relationship()


class MatchPrediction(Base):
    __tablename__ = "match_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("tournament_matches.id"), nullable=False, unique=True, index=True)
    home_win_probability: Mapped[float] = mapped_column(Float, nullable=False)
    draw_probability: Mapped[float] = mapped_column(Float, nullable=False)
    away_win_probability: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_home_score: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_away_score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[str] = mapped_column(String(24), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    match: Mapped[TournamentMatch] = relationship()


class TeamRating(Base):
    __tablename__ = "team_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    rating_date: Mapped[Date] = mapped_column(Date, nullable=False)
    elo_rating: Mapped[float] = mapped_column(Float, nullable=False)
    fifa_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    fifa_points: Mapped[float] = mapped_column(Float, nullable=False)

    team: Mapped[Team] = relationship(back_populates="ratings")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_a_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    team_b_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    match_date: Mapped[Date] = mapped_column(Date, nullable=False)
    team_a_win_probability: Mapped[float] = mapped_column(Float, nullable=False)
    draw_probability: Mapped[float] = mapped_column(Float, nullable=False)
    team_b_win_probability: Mapped[float] = mapped_column(Float, nullable=False)
    expected_goals_team_a: Mapped[float] = mapped_column(Float, nullable=False)
    expected_goals_team_b: Mapped[float] = mapped_column(Float, nullable=False)
    most_likely_scorelines: Mapped[list[dict[str, float | str]]] = mapped_column(JsonType, nullable=False)
    confidence: Mapped[str] = mapped_column(String(24), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ModelRun(Base):
    __tablename__ = "model_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    training_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    training_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metrics: Mapped[dict[str, float | int | str]] = mapped_column(JsonType, default=dict, nullable=False)
    mlflow_run_id: Mapped[str | None] = mapped_column(String(120))
