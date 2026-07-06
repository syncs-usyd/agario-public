from helper.client_state import ClientSate
from helper.state_mutator import StateMutator
from lib.interface.events.event_game_started import PublicEventGameStarted
from lib.interface.events.event_player_won import EventPlayerWon
from lib.models.blob_model import BlobModel
from lib.models.player_model import PlayerModel, PublicPlayerModel


def test_client_state_exposes_me_but_not_players() -> None:
    state = ClientSate()

    assert not hasattr(state, "players")


def test_public_game_started_populates_me_and_total_players() -> None:
    state = ClientSate()
    mutator = StateMutator(state)
    event = PublicEventGameStarted(
        turn_order=[0, 1, 2, 3],
        arena_size=60.0,
        vision_size=20.0,
        turn_duration_seconds=0.1,
        max_rounds=250,
        players=[
            PublicPlayerModel(player_id=0, alive=True),
            PublicPlayerModel(player_id=1, alive=True),
            PublicPlayerModel(player_id=2, alive=True),
            PublicPlayerModel(player_id=3, alive=True),
        ],
        you=PlayerModel(
            player_id=2,
            team_id=2,
            pos=(12.0, 18.0),
            radius=3.5,
            alive=True,
            blobs=(BlobModel(blob_id=7, pos=(12.0, 18.0), radius=3.5),),
        ),
    )

    mutator.commit(0, event)

    assert state.total_players == 4
    assert state.me.player_id == 2
    assert state.me.x == 12.0
    assert state.me.y == 18.0
    assert state.me.radius == 3.5
    assert not hasattr(state, "players")


def test_player_won_sets_public_winner_id() -> None:
    state = ClientSate()
    mutator = StateMutator(state)

    mutator.commit(0, EventPlayerWon(player_id=1))

    assert state.game_over
    assert state.winner_player_id == 1
