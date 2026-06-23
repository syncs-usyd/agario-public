from lib.game.game_logic import GameLogic
from lib.interact.map import Map
from lib.interface.events.typing import EventType
from lib.models.blob_model import VisibleBlobModel
from lib.models.food_model import FoodModel
from lib.models.virus_model import VirusModel
from helper.state.client_player_state import ClientPlayer

from copy import deepcopy


class ClientSate(GameLogic):
    def __init__(self) -> None:
        self.round = -1
        self.max_rounds = 0
        self.players: dict[int, ClientPlayer]
        self.map = Map()
        self.vision_size = 0.0
        self.view_center = (0.0, 0.0)
        self.turn_duration_seconds = 0.0
        self.visible_food: list[FoodModel] = []
        self.visible_blobs: list[VisibleBlobModel] = []
        self.visible_viruses: list[VirusModel] = []

        self.game_over = False

        self.event_history: list["EventType"] = []
        self.new_events: int = 0
        self.turn_order: list[int] = []

        self.me: ClientPlayer
