from typing import TYPE_CHECKING, Optional

from lib.interface.events.event_game_started import (
    EventGameStarted,
    PublicEventGameStarted,
)
from lib.interface.events.event_player_eaten import EventPlayerEaten
from lib.interface.events.event_player_moved import EventPlayerMoved
from lib.interface.events.typing import EventType

if TYPE_CHECKING:
    from engine.state.game_state import GameState


class CensorEvent:
    def __init__(self, state: "GameState") -> None:
        self.state = state

    def censor(self, event: EventType, player_id: int) -> Optional[EventType]:
        match event:
            case EventGameStarted() as e:
                return PublicEventGameStarted(
                    turn_order=e.turn_order,
                    arena_size=e.arena_size,
                    vision_size=self.state.get_player_vision_size(player_id),
                    turn_duration_seconds=e.turn_duration_seconds,
                    max_rounds=e.max_rounds,
                    players=[player.get_public() for player in e.players],
                    you=filter(
                        lambda x: x.player_id == player_id, e.players
                    ).__next__(),
                )
            case EventPlayerMoved() as e:
                if e.player_id == player_id:
                    return e

                visible_blobs = tuple(
                    blob
                    for blob in e.blobs
                    if self.state.player_can_see_point(
                        player_id,
                        blob.pos[0],
                        blob.pos[1],
                    )
                )
                if visible_blobs:
                    total_mass = sum(blob.radius * blob.radius for blob in visible_blobs)
                    pos = (
                        sum(blob.pos[0] * blob.radius * blob.radius for blob in visible_blobs)
                        / total_mass,
                        sum(blob.pos[1] * blob.radius * blob.radius for blob in visible_blobs)
                        / total_mass,
                    )
                    return EventPlayerMoved(
                        player_id=e.player_id,
                        pos=pos,
                        radius=total_mass ** 0.5,
                        alive=e.alive,
                        blobs=visible_blobs,
                    )
                return None
            case EventPlayerEaten() as e:
                if (
                    player_id in (e.eater_player_id, e.eaten_player_id)
                    or self.state.player_can_see_point(
                        player_id,
                        e.eater_pos[0],
                        e.eater_pos[1],
                    )
                    or self.state.player_can_see_point(
                        player_id,
                        e.eaten_pos[0],
                        e.eaten_pos[1],
                    )
                ):
                    return e
                return None

        return event
