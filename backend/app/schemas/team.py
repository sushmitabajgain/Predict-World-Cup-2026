from pydantic import BaseModel, ConfigDict


class TeamRead(BaseModel):
    id: int
    name: str
    fifa_code: str
    confederation: str

    model_config = ConfigDict(from_attributes=True)
