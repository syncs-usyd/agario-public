from helper.client_state import ClientSate
from helper.state.client_player_state import ClientPlayer

from lib.interface.events.event_player_bannned import EventPlayerBanned
from lib.interface.events.event_player_eaten import EventPlayerEaten
from lib.interface.events.event_player_moved import EventPlayerMoved
from lib.interface.events.event_player_won import EventPlayerWon
from lib.interface.events.event_game_ended import (
    EventGameEndedCancelled,
)
from lib.interface.events.event_game_started import (
    PublicEventGameStarted,
)
from lib.interface.events.moves.move_player import MovePlayer
from lib.interface.events.typing import EventType


import logging

# Configure logging to display INFO messages and write to a file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    filename='app1.log',
    filemode='w' # Use 'w' to overwrite each time
)


class StateMutator:
    def __init__(self, state: ClientSate) -> None:
        self.state = state

    def commit(self, i: int, event: EventType) -> None:
        self.state.event_history.append(event)

        match event:
            case PublicEventGameStarted() as e:
                self.state.turn_order = e.turn_order
                self.state.map.size = e.arena_size
                self.state.vision_size = e.vision_size
                self.state.view_center = e.you.pos
                self.state.turn_duration_seconds = e.turn_duration_seconds
                self.state.max_rounds = e.max_rounds
                self.state.players = {p.player_id: ClientPlayer(p) for p in e.players}
                self.state.me = self.state.players[e.you.player_id]
                self.state.me.sync_from_model(e.you)

            case EventPlayerMoved() as e:
                player = self.state.players[e.player_id]
                player.sync_snapshot(
                    pos=e.pos,
                    radius=e.radius,
                    alive=e.alive,
                    blobs=e.blobs,
                )

            case EventPlayerEaten() as e:
                eater = self.state.players[e.eater_player_id]
                eater_blob = eater.blobs.get(e.eater_blob_id)
                if eater_blob is not None:
                    eater_blob.radius = e.eater_radius

                eaten = self.state.players[e.eaten_player_id]
                eaten.blobs.pop(e.eaten_blob_id, None)
                eaten.alive = e.eaten_player_alive

            case EventGameEndedCancelled() as e:
                self.state.game_over = True

            case EventPlayerBanned() as e:
                self.state.game_over = True

            case EventPlayerWon() as e:
                self.state.game_over = True

            case MovePlayer() as e:
                pass

            case _:
                raise RuntimeError(f"Unrecognised event: {event}")
