from pydantic import BaseModel


class BlobModel(BaseModel):
    blob_id: int
    pos: tuple[float, float]
    radius: float
    merge_cooldown: int = 0


class VisibleBlobModel(BlobModel):
    player_id: int
    team_id: int
