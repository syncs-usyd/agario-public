import json

from engine.interface.io.censor_event import CensorEvent
from engine.state.game_state import GameState
from lib.config.arena import NUM_PLAYERS
from lib.interface.events.moves.move_player import MovePlayer
from lib.models.penguin_model import DirectionModel


def _make_state(tmp_path, monkeypatch) -> GameState:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "input").mkdir()
    (tmp_path / "output").mkdir()
    with open(tmp_path / "input" / "catalog.json", "w") as file:
        json.dump([{"team_id": index} for index in range(NUM_PLAYERS)], file)
    return GameState()


def test_move_player_is_only_visible_to_the_issuing_player(
    tmp_path, monkeypatch
) -> None:
    state = _make_state(tmp_path, monkeypatch)
    censor = CensorEvent(state)
    move = MovePlayer(
        player_id=1,
        direction=DirectionModel(x=1.0, y=0.0),
        split=True,
    )

    assert censor.censor(move, player_id=1) == move
    assert censor.censor(move, player_id=0) is None

