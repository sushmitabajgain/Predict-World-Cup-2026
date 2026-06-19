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
