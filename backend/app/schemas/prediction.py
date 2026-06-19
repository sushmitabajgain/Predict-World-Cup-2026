from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


VenueType = Literal["home", "away", "neutral"]


class PredictionRequest(BaseModel):
    team_a: str = Field(min_length=2, max_length=120)
    team_b: str = Field(min_length=2, max_length=120)
    venue_type: VenueType = "neutral"
    match_date: date

    @model_validator(mode="after")
    def teams_must_differ(self) -> "PredictionRequest":
        if self.team_a.strip().casefold() == self.team_b.strip().casefold():
            raise ValueError("Team A and Team B must be different")
        self.team_a = self.team_a.strip()
        self.team_b = self.team_b.strip()
        return self


class ScorelineProbability(BaseModel):
    score: str
    probability: float


class PredictionBase(BaseModel):
    team_a: str
    team_b: str
    team_a_win_probability: float
    draw_probability: float
    team_b_win_probability: float
    expected_goals_team_a: float
    expected_goals_team_b: float
    most_likely_scorelines: list[ScorelineProbability]
    confidence: str
    explanation: str
    model_version: str
    created_at: datetime


class PredictionResponse(PredictionBase):
    pass


class PredictionCreate(PredictionBase):
    team_a_id: int
    team_b_id: int
    match_date: date


class PredictionRead(PredictionBase):
    id: int
    match_date: date

    model_config = ConfigDict(from_attributes=True)
