"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("fifa_code", sa.String(length=3), nullable=False),
        sa.Column("confederation", sa.String(length=32), nullable=False),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("fifa_code"),
    )
    op.create_index("ix_teams_id", "teams", ["id"])
    op.create_index("ix_teams_name", "teams", ["name"])

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_date", sa.Date(), nullable=False),
        sa.Column("team_a_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("team_b_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("score_a", sa.Integer(), nullable=False),
        sa.Column("score_b", sa.Integer(), nullable=False),
        sa.Column("competition", sa.String(length=120), nullable=False),
        sa.Column("venue", sa.String(length=120), nullable=False),
        sa.Column("venue_type", sa.String(length=24), nullable=False),
        sa.Column("is_neutral", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_matches_match_date", "matches", ["match_date"])

    op.create_table(
        "team_ratings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("rating_date", sa.Date(), nullable=False),
        sa.Column("elo_rating", sa.Float(), nullable=False),
        sa.Column("fifa_rank", sa.Integer(), nullable=False),
        sa.Column("fifa_points", sa.Float(), nullable=False),
    )
    op.create_index("ix_team_ratings_team_id", "team_ratings", ["team_id"])

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("team_a_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("team_b_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("match_date", sa.Date(), nullable=False),
        sa.Column("team_a_win_probability", sa.Float(), nullable=False),
        sa.Column("draw_probability", sa.Float(), nullable=False),
        sa.Column("team_b_win_probability", sa.Float(), nullable=False),
        sa.Column("expected_goals_team_a", sa.Float(), nullable=False),
        sa.Column("expected_goals_team_b", sa.Float(), nullable=False),
        sa.Column("most_likely_scorelines", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("confidence", sa.String(length=24), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_predictions_team_a_id", "predictions", ["team_a_id"])
    op.create_index("ix_predictions_team_b_id", "predictions", ["team_b_id"])

    op.create_table(
        "model_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("training_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("training_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("mlflow_run_id", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("model_runs")
    op.drop_index("ix_predictions_team_b_id", table_name="predictions")
    op.drop_index("ix_predictions_team_a_id", table_name="predictions")
    op.drop_table("predictions")
    op.drop_index("ix_team_ratings_team_id", table_name="team_ratings")
    op.drop_table("team_ratings")
    op.drop_index("ix_matches_match_date", table_name="matches")
    op.drop_table("matches")
    op.drop_index("ix_teams_name", table_name="teams")
    op.drop_index("ix_teams_id", table_name="teams")
    op.drop_table("teams")
