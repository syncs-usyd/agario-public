import math
import random
from lib.config.arena import (
    FOOD_COUNT,
    MAX_ROUNDS,
    NUM_PLAYERS,
    PLAYER_SPAWN_PADDING,
    VIRUS_COUNT,
    VIRUS_SIZE,
    VISION_SIZE,
    VISION_REFERENCE_SUM_OF_RADII,
)
from engine.state.player_state import PlayerState
from engine.config.io_config import CORE_DIRECTORY

from lib.game.game_logic import GameLogic
from lib.interact.map import Map
from lib.interface.events.typing import EventType
from lib.models.food_model import FoodModel
from lib.models.blob_model import BlobModel, VisibleBlobModel
from lib.models.virus_model import VirusModel
from lib.config.player import STARTING_RADIUS

import json


class GameState(GameLogic):
    def __init__(self) -> None:
        with open(f"{CORE_DIRECTORY}/input/catalog.json", "r") as f:
            self.catalog = json.load(f)

        self.round = -1
        self.max_rounds = MAX_ROUNDS
        self.players: dict[int, PlayerState] = {
            i: PlayerState(i, self.catalog[i]["team_id"]) for i in range(NUM_PLAYERS)
        }
        self.map = Map()
        self._spawn_players_in_corners()
        self._ensure_food_count()
        self._ensure_virus_count()

        self.event_history: list[EventType] = []
        self.private_event_history: list[EventType] = []
        self.turn_order: list[int] = []

    def _spawn_players_in_corners(self) -> None:
        """Spawn players in corners: 0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right."""
        padding = max(PLAYER_SPAWN_PADDING, STARTING_RADIUS * 2)
        corner_positions = [
            (padding, padding),                                  # Player 0: top-left
            (self.map.size - padding, padding),                  # Player 1: top-right
            (padding, self.map.size - padding),                  # Player 2: bottom-left
            (self.map.size - padding, self.map.size - padding),  # Player 3: bottom-right
        ]

        for player_id, player in self.players.items():
            spawn_blob = player.blobs[0]
            x, y = corner_positions[player_id]
            spawn_blob.x = x
            spawn_blob.y = y

    def _connect_players(self) -> None:
        for player in self.players.values():
            player.connect()

    def _ensure_food_count(self) -> list[FoodModel]:
        spawned: list[FoodModel] = []
        while len(self.map.foods) < FOOD_COUNT:
            spawned.append(self.map.spawn_food())
        return spawned

    def _can_place_virus(self, x: float, y: float, radius: float) -> bool:
        for virus in self.map.viruses:
            dx = virus.pos[0] - x
            dy = virus.pos[1] - y
            min_distance = virus.radius + radius
            if dx * dx + dy * dy < min_distance * min_distance:
                return False

        for player in self.players.values():
            for blob in player.blobs.values():
                dx = blob.x - x
                dy = blob.y - y
                min_distance = blob.radius + radius
                if dx * dx + dy * dy < min_distance * min_distance:
                    return False

        return True

    def _ensure_virus_count(self) -> list[VirusModel]:
        spawned: list[VirusModel] = []
        while len(self.map.viruses) < VIRUS_COUNT:
            for _ in range(10000):
                x = random.uniform(VIRUS_SIZE, self.map.size - VIRUS_SIZE)
                y = random.uniform(VIRUS_SIZE, self.map.size - VIRUS_SIZE)
                if self._can_place_virus(x, y, VIRUS_SIZE):
                    spawned.append(
                        self.map.spawn_virus(pos=(x, y), radius=VIRUS_SIZE)
                    )
                    break
            else:
                raise RuntimeError("Could not place all viruses in the arena.")
        return spawned

    def is_in_vision(
        self,
        observer_x: float,
        observer_y: float,
        vision_size: float,
        target_x: float,
        target_y: float,
    ) -> bool:
        half_vision = vision_size / 2
        return (
            abs(target_x - observer_x) <= half_vision
            and abs(target_y - observer_y) <= half_vision
        )

    def get_player_view_center(self, player_id: int) -> tuple[float, float]:
        player = self.players[player_id]
        return (player.x, player.y)

    def get_player_vision_size(self, player_id: int) -> float:
        player = self.players[player_id]
        if not player.alive:
            return VISION_SIZE

        sum_of_radii = sum(blob.radius for blob in player.blobs.values())
        if sum_of_radii <= 0:
            return VISION_SIZE

        scale = math.pow(
            max(sum_of_radii / VISION_REFERENCE_SUM_OF_RADII, 1.0),
            0.4,
        )
        return scale * VISION_SIZE

    def player_can_see_point(
        self, player_id: int, target_x: float, target_y: float
    ) -> bool:
        player = self.players[player_id]
        if not player.alive:
            return False
        center_x, center_y = self.get_player_view_center(player_id)
        vision_size = self.get_player_vision_size(player_id)
        return self.is_in_vision(
            center_x,
            center_y,
            vision_size,
            target_x,
            target_y,
        )

    def get_visible_food(self, player_id: int) -> list[FoodModel]:
        if not self.players[player_id].alive:
            return []
        visible_food: list[FoodModel] = []
        for food in self.map.foods:
            if self.player_can_see_point(player_id, food.pos[0], food.pos[1]):
                visible_food.append(food)
        return visible_food

    def get_visible_viruses(self, player_id: int) -> list[VirusModel]:
        if not self.players[player_id].alive:
            return []
        visible_viruses: list[VirusModel] = []
        for virus in self.map.viruses:
            if self.player_can_see_point(player_id, virus.pos[0], virus.pos[1]):
                visible_viruses.append(virus)
        return visible_viruses

    def get_visible_player_blobs(
        self, target_id: int, viewer_id: int
    ) -> list[BlobModel]:
        target = self.players[target_id]
        if not target.alive:
            return []
        visible_blobs: list[BlobModel] = []
        for blob in target.sorted_blobs():
            if self.player_can_see_point(viewer_id, blob.x, blob.y):
                visible_blobs.append(blob._to_model())
        return visible_blobs

    def get_visible_blobs(self, player_id: int) -> list[VisibleBlobModel]:
        if not self.players[player_id].alive:
            return []
        visible_players: list[VisibleBlobModel] = []
        for other in self.players.values():
            if other.id == player_id or not other.alive:
                continue
            for blob in other.sorted_blobs():
                if self.player_can_see_point(player_id, blob.x, blob.y):
                    visible_players.append(
                        blob._to_visible_model(
                            player_id=other.id,
                            team_id=other.team_id,
                        )
                    )
        return visible_players

    def player_is_visible_to(self, target_id: int, viewer_id: int) -> bool:
        target = self.players[target_id]
        return any(
            self.player_can_see_point(viewer_id, blob.x, blob.y)
            for blob in target.blobs.values()
        )

    def living_players(self) -> list[PlayerState]:
        return [player for player in self.players.values() if player.alive]

    def get_rankings(self) -> list[int]:
        return [
            player.id
            for player in sorted(
                self.players.values(),
                key=lambda p: (1 if p.alive else 0, p.radius, p.round_died),
                reverse=True,
            )
        ]

    def is_game_over(self) -> bool:
        return self.round + 1 >= self.max_rounds or len(self.living_players()) <= 1
