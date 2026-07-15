from collections.abc import Mapping, Sequence

from engine.interface.io.exceptions import (
    BrokenPipeException,
    CumulativeTimeoutException,
    InvalidMessageException,
    InvalidMoveException,
    PlayerException,
    TimeoutException,
)
from lib.interface.events.event_player_bannned import EventPlayerBanned
from lib.interface.io.ban_type import BanType
from lib.interface.queries.query_move import QueryMovePlayer
from pydantic import BaseModel

MAX_DETAIL_DEPTH = 3
MAX_DETAIL_ITEMS = 12
MAX_DETAIL_STRING_LENGTH = 240


def _truncate_string(value: str) -> str:
    if len(value) <= MAX_DETAIL_STRING_LENGTH:
        return value
    return value[: MAX_DETAIL_STRING_LENGTH - 3] + "..."


def _serialise_detail(value: object, depth: int = 0) -> object:
    if depth >= MAX_DETAIL_DEPTH:
        return _truncate_string(repr(value))

    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        return _truncate_string(value)

    if isinstance(value, QueryMovePlayer):
        update_events = list(value.update.values())
        return {
            "query_type": value.query_type,
            "round": value.round,
            "update_count": len(value.update),
            "update_event_types": [
                event.event_type for event in update_events[:MAX_DETAIL_ITEMS]
            ],
            "rankings": list(value.rankings),
            "you": {
                "player_id": value.you.player_id,
                "team_id": value.you.team_id,
                "alive": value.you.alive,
                "radius": value.you.radius,
                "blob_count": len(value.you.blobs),
            },
            "view_center": list(value.view_center),
            "vision_size": value.vision_size,
            "visible_food_count": len(value.visible_food),
            "visible_blob_count": len(value.visible_blobs),
            "visible_virus_count": len(value.visible_viruses),
        }

    if isinstance(value, BaseModel):
        return _serialise_detail(value.model_dump(mode="json"), depth + 1)

    if isinstance(value, Mapping):
        items = list(value.items())
        result = {
            _truncate_string(str(key)): _serialise_detail(item, depth + 1)
            for key, item in items[:MAX_DETAIL_ITEMS]
        }
        if len(items) > MAX_DETAIL_ITEMS:
            result["__truncated_items__"] = len(items) - MAX_DETAIL_ITEMS
        return result

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        items = list(value)
        result = [_serialise_detail(item, depth + 1) for item in items[:MAX_DETAIL_ITEMS]]
        if len(items) > MAX_DETAIL_ITEMS:
            result.append({"__truncated_items__": len(items) - MAX_DETAIL_ITEMS})
        return result

    return _truncate_string(repr(value))


def event_banned_factory(e: PlayerException) -> "EventPlayerBanned":
    ban_type: BanType
    details = _serialise_detail(e.details)
    match e:
        case TimeoutException() as e:
            ban_type = "TIMEOUT"
        case CumulativeTimeoutException() as e:
            ban_type = "CUMULATIVE_TIMEOUT"
        case BrokenPipeException():
            ban_type = "BROKEN_PIPE"
        case InvalidMessageException() as e:
            ban_type = "INVALID_MESSAGE"
        case InvalidMoveException() as e:
            ban_type = "INVALID_MOVE"
        case _:
            raise RuntimeError("An unspecified PlayerException was raised.")

    return EventPlayerBanned(
        player_id=e.player_id,
        reason=e.error_message,
        ban_type=ban_type,
        details=details,
    )
