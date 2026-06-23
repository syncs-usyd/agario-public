from pydantic import BaseModel

from lib.models.blob_model import BlobModel


class RelativeFoodModel(BaseModel):
    dx: float
    dy: float


class VisiblePlayerModel(BaseModel):
    player_id: int
    dx: float
    dy: float
    radius: float
    alive: bool

class PlayerModel(BaseModel):
    player_id: int
    team_id: int
    pos: tuple[float, float]
    radius: float
    alive: bool
    blobs: tuple[BlobModel, ...] = ()

    def get_public(self) -> "PublicPlayerModel":
        return PublicPlayerModel(
            player_id=self.player_id,
            alive=self.alive,
        )


class PublicPlayerModel(BaseModel):
    player_id: int
    alive: bool
