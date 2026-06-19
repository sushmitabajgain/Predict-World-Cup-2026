from sqlalchemy import select

from app.ml.features import FEATURE_COLUMNS, build_match_features
from app.models.entities import Team


def test_feature_builder_returns_expected_columns(db_session):
    brazil = db_session.scalar(select(Team).where(Team.name == "Brazil"))
    scotland = db_session.scalar(select(Team).where(Team.name == "Scotland"))
    features = build_match_features(db_session, brazil, scotland, "neutral", __import__("datetime").date(2026, 6, 24))

    assert list(features.keys()) == FEATURE_COLUMNS
    assert features["elo_diff"] > 0
    assert features["venue_neutral"] == 1.0
