from pydantic import BaseModel


class VirusModel(BaseModel):
    virus_id: int
    pos: tuple[float, float]
    radius: float
