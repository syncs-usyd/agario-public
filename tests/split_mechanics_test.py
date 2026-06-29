import math
import json

from engine.state.blob_state import BlobState
from engine.state.game_state import GameState
from engine.state.state_mutator import StateMutator
from lib.config.arena import (
    MAX_BLOB_COUNT,
    NUM_PLAYERS,
    VISION_REFERENCE_SUM_OF_RADII,
    VISION_SIZE,
    VIRUS_COUNT,
)
from lib.config.player import SAME_PLAYER_OVERLAP_EPSILON, SPLIT_MIN_MASS
from lib.interface.events.moves.move_player import MovePlayer
from lib.models.penguin_model import DirectionModel


def _make_state(tmp_path, monkeypatch) -> GameState:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "input").mkdir()
    (tmp_path / "output").mkdir()
    with open(tmp_path / "input" / "catalog.json", "w") as file:
        json.dump([{"team_id": index} for index in range(NUM_PLAYERS)], file)
    return GameState()


def _is_overlapping(blob_a: BlobState, blob_b: BlobState) -> bool:
    distance = math.hypot(blob_a.x - blob_b.x, blob_a.y - blob_b.y)
    return distance + SAME_PLAYER_OVERLAP_EPSILON < blob_a.radius + blob_b.radius


def test_split_hits_each_eligible_blob_and_conserves_mass(tmp_path, monkeypatch) -> None:
    state = _make_state(tmp_path, monkeypatch)
    mutator = StateMutator(state)
    player = state.players[0]
    state.map.foods = []
    state.map.viruses = []

    for other_id, other in state.players.items():
        if other_id != player.id:
            other.blobs.clear()

    eligible_mass = SPLIT_MIN_MASS + 1.0
    player.blobs = {
        0: BlobState(blob_id=0, x=10.0, y=10.0, radius=math.sqrt(eligible_mass)),
        1: BlobState(blob_id=1, x=14.0, y=10.0, radius=math.sqrt(eligible_mass)),
        2: BlobState(
            blob_id=2,
            x=18.0,
            y=10.0,
            radius=math.sqrt(SPLIT_MIN_MASS) - 0.05,
        ),
    }

    total_mass_before = sum(blob.mass for blob in player.blobs.values())
    mutator.commit_round(
        [
            MovePlayer(
                player_id=player.id,
                direction=DirectionModel(x=1.0, y=0.0),
                split=True,
            )
        ]
    )

    assert len(player.blobs) == 5
    total_mass_after = sum(blob.mass for blob in player.blobs.values())
    assert math.isclose(total_mass_before, total_mass_after, rel_tol=1e-9)

    split_children = [blob for blob in player.blobs.values() if blob.blob_id >= 3]
    assert len(split_children) == 2
    for child in split_children:
        assert child.merge_cooldown > 0


def test_same_player_cooldown_blocks_merge_until_ready(tmp_path, monkeypatch) -> None:
    state = _make_state(tmp_path, monkeypatch)
    mutator = StateMutator(state)
    player = state.players[0]
    state.map.foods = []
    state.map.viruses = []

    for other_id, other in state.players.items():
        if other_id != player.id:
            other.blobs.clear()

    player.blobs = {
        0: BlobState(
            blob_id=0,
            x=20.0,
            y=20.0,
            radius=1.0,
            merge_cooldown=3,
        ),
        1: BlobState(
            blob_id=1,
            x=21.5,
            y=20.0,
            radius=1.0,
            merge_cooldown=3,
        ),
    }

    mutator.commit_round(
        [
            MovePlayer(
                player_id=player.id,
                direction=DirectionModel(x=0.0, y=0.0),
            )
        ]
    )

    assert len(player.blobs) == 2
    blob_a, blob_b = player.sorted_blobs()
    assert not _is_overlapping(blob_a, blob_b)

    for blob in player.blobs.values():
        blob.merge_cooldown = 0
    state.map.foods = []
    player.blobs[0].x = 20.0
    player.blobs[0].y = 20.0
    player.blobs[1].x = 21.5
    player.blobs[1].y = 20.0

    mutator.commit_round(
        [
            MovePlayer(
                player_id=player.id,
                direction=DirectionModel(x=0.0, y=0.0),
            )
        ]
    )

    assert len(player.blobs) == 1
    merged_blob = next(iter(player.blobs.values()))
    assert math.isclose(merged_blob.radius, math.sqrt(2.0), rel_tol=1e-9)


def test_view_center_and_visibility_use_player_centroid(tmp_path, monkeypatch) -> None:
    state = _make_state(tmp_path, monkeypatch)
    player = state.players[0]
    state.map.viruses = []

    player.blobs = {
        0: BlobState(blob_id=0, x=10.0, y=10.0, radius=1.0),
        1: BlobState(blob_id=1, x=30.0, y=10.0, radius=1.0),
    }

    assert state.get_player_view_center(player.id) == (20.0, 10.0)
    assert math.isclose(state.get_player_vision_size(player.id), VISION_SIZE, rel_tol=1e-9)

    assert state.player_can_see_point(player.id, 23.5, 10.0)
    assert not state.player_can_see_point(player.id, 9.9, 10.0)


def test_vision_size_scales_from_sum_of_blob_radii(tmp_path, monkeypatch) -> None:
    state = _make_state(tmp_path, monkeypatch)
    player = state.players[0]
    state.map.viruses = []

    player.blobs = {
        0: BlobState(blob_id=0, x=10.0, y=10.0, radius=64.0),
        1: BlobState(blob_id=1, x=20.0, y=20.0, radius=64.0),
    }

    expected = (
        math.pow(max(128.0 / VISION_REFERENCE_SUM_OF_RADII, 1.0), 0.4) * VISION_SIZE
    )
    assert math.isclose(state.get_player_vision_size(player.id), expected, rel_tol=1e-9)


def test_split_respects_max_blob_count(tmp_path, monkeypatch) -> None:
    state = _make_state(tmp_path, monkeypatch)
    mutator = StateMutator(state)
    player = state.players[0]
    state.map.foods = []
    state.map.viruses = []

    for other_id, other in state.players.items():
        if other_id != player.id:
            other.blobs.clear()

    eligible_mass = SPLIT_MIN_MASS + 1.0
    player.blobs = {
        blob_id: BlobState(
            blob_id=blob_id,
            x=10.0 + blob_id,
            y=10.0,
            radius=math.sqrt(eligible_mass),
            merge_cooldown=5,
        )
        for blob_id in range(MAX_BLOB_COUNT)
    }

    total_mass_before = sum(blob.mass for blob in player.blobs.values())
    mutator.commit_round(
        [
            MovePlayer(
                player_id=player.id,
                direction=DirectionModel(x=1.0, y=0.0),
                split=True,
            )
        ]
    )

    assert len(player.blobs) == MAX_BLOB_COUNT
    total_mass_after = sum(blob.mass for blob in player.blobs.values())
    assert math.isclose(total_mass_before, total_mass_after, rel_tol=1e-9)


def test_virus_pop_adds_mass_and_splits_up_to_cap(tmp_path, monkeypatch) -> None:
    state = _make_state(tmp_path, monkeypatch)
    mutator = StateMutator(state)
    player = state.players[0]
    state.map.foods = []
    state.map.viruses = []

    for other_id, other in state.players.items():
        if other_id != player.id:
            other.blobs.clear()

    player.blobs = {
        0: BlobState(blob_id=0, x=20.0, y=20.0, radius=2.0),
    }
    state.map.spawn_virus(pos=(20.0, 20.0), radius=2.0)

    mutator.commit_round(
        [
            MovePlayer(
                player_id=player.id,
                direction=DirectionModel(x=0.0, y=0.0),
            )
        ]
    )

    assert len(player.blobs) == MAX_BLOB_COUNT
    assert len(state.map.viruses) == VIRUS_COUNT
    expected_total_mass = 4.0 + 2.0
    total_mass_after = sum(blob.mass for blob in player.blobs.values())
    assert math.isclose(total_mass_after, expected_total_mass, rel_tol=1e-9)

    expected_piece_radius = math.sqrt(expected_total_mass / MAX_BLOB_COUNT)
    for blob in player.blobs.values():
        assert math.isclose(blob.radius, expected_piece_radius, rel_tol=1e-9)
        assert blob.merge_cooldown > 0


def test_virus_does_not_pop_when_blob_is_not_large_enough(tmp_path, monkeypatch) -> None:
    state = _make_state(tmp_path, monkeypatch)
    mutator = StateMutator(state)
    player = state.players[0]
    state.map.foods = []
    state.map.viruses = []

    for other_id, other in state.players.items():
        if other_id != player.id:
            other.blobs.clear()

    player.blobs = {
        0: BlobState(blob_id=0, x=20.0, y=20.0, radius=1.4),
    }
    state.map.spawn_virus(pos=(20.0, 20.0), radius=2.0)

    total_mass_before = sum(blob.mass for blob in player.blobs.values())
    mutator.commit_round(
        [
            MovePlayer(
                player_id=player.id,
                direction=DirectionModel(x=0.0, y=0.0),
            )
        ]
    )

    assert len(player.blobs) == 1
    assert len(state.map.viruses) == VIRUS_COUNT
    total_mass_after = sum(blob.mass for blob in player.blobs.values())
    assert math.isclose(total_mass_after, total_mass_before, rel_tol=1e-9)
