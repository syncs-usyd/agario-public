import json
import os
from signal import SIGCONT, SIGSTOP
from types import SimpleNamespace

from engine.game_engine import GameEngine
from engine.interface.io.process_groups import (
    PROCESS_GROUPS_FILENAME,
    ProcessGroupController,
)


def test_process_group_controller_loads_metadata(tmp_path) -> None:
    with open(tmp_path / PROCESS_GROUPS_FILENAME, "w") as process_groups_file:
        json.dump(
            [
                {"player_id": 0, "pgid": 111},
                {"player_id": 2, "pgid": 222},
                {"player_id": "bad", "pgid": 333},
            ],
            process_groups_file,
        )

    controller = ProcessGroupController.from_core_directory(str(tmp_path))

    assert controller._process_groups == {0: 111, 2: 222}


def test_process_group_controller_signals_players(monkeypatch) -> None:
    calls: list[tuple[int, int]] = []
    monkeypatch.setattr(os, "killpg", lambda pgid, sig: calls.append((pgid, sig)))
    controller = ProcessGroupController({0: 101, 1: 202, 2: 202})

    controller.pause_player(0)
    controller.resume_player(1)
    controller.pause_all()

    assert calls == [
        (101, SIGSTOP),
        (202, SIGCONT),
        (101, SIGSTOP),
        (202, SIGSTOP),
    ]


def test_query_move_for_player_pauses_after_query() -> None:
    calls: list[tuple[str, int]] = []
    engine = GameEngine.__new__(GameEngine)
    engine.state = SimpleNamespace(
        players={
            3: SimpleNamespace(
                connection=SimpleNamespace(
                    query_move_player=lambda state, validator, censor: (
                        calls.append(("query", 3)) or "move"
                    )
                )
            )
        }
    )
    engine.validator = object()
    engine.censor = object()
    engine.process_groups = SimpleNamespace(
        resume_player=lambda player_id: calls.append(("resume", player_id)),
        pause_player=lambda player_id: calls.append(("pause", player_id)),
    )

    result = GameEngine._query_move_for_player(engine, 3)

    assert result == "move"
    assert calls == [("resume", 3), ("query", 3), ("pause", 3)]


def test_query_move_for_player_pauses_after_exception() -> None:
    calls: list[tuple[str, int]] = []
    engine = GameEngine.__new__(GameEngine)

    def raise_error(*_) -> None:
        calls.append(("query", 4))
        raise RuntimeError("boom")

    engine.state = SimpleNamespace(
        players={4: SimpleNamespace(connection=SimpleNamespace(query_move_player=raise_error))}
    )
    engine.validator = object()
    engine.censor = object()
    engine.process_groups = SimpleNamespace(
        resume_player=lambda player_id: calls.append(("resume", player_id)),
        pause_player=lambda player_id: calls.append(("pause", player_id)),
    )

    try:
        GameEngine._query_move_for_player(engine, 4)
    except RuntimeError as error:
        assert str(error) == "boom"
    else:
        assert False, "expected RuntimeError"

    assert calls == [("resume", 4), ("query", 4), ("pause", 4)]
