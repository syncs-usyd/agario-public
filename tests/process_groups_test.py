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
    cgroup_dir = tmp_path / "submission0"
    cgroup_dir.mkdir()
    with open(cgroup_dir / "cpu.stat", "w") as cpu_stat_file:
        cpu_stat_file.write("usage_usec 17\n")

    with open(tmp_path / PROCESS_GROUPS_FILENAME, "w") as process_groups_file:
        json.dump(
            [
                {"player_id": 0, "pgid": 111, "cgroup_path": str(cgroup_dir)},
                {"player_id": 2, "pgid": 222},
                {"player_id": "bad", "pgid": 333},
            ],
            process_groups_file,
        )

    controller = ProcessGroupController.from_core_directory(str(tmp_path))

    assert controller._process_groups == {0: 111, 2: 222}
    assert controller._cgroup_paths == {0: str(cgroup_dir)}


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


def test_process_group_controller_reads_cpu_usage(tmp_path) -> None:
    cgroup_dir = tmp_path / "submission4"
    cgroup_dir.mkdir()
    with open(cgroup_dir / "cpu.stat", "w") as cpu_stat_file:
        cpu_stat_file.write("usage_usec 12345\nuser_usec 6789\nsystem_usec 5556\n")

    controller = ProcessGroupController({4: 404}, {4: str(cgroup_dir)})

    assert controller.get_cpu_usage_usec(4) == 12345


def test_process_group_controller_requires_cgroup_metadata() -> None:
    controller = ProcessGroupController({4: 404})

    try:
        controller.get_cpu_usage_usec(4)
    except RuntimeError as error:
        assert "missing cgroup metadata" in str(error)
    else:
        assert False, "expected RuntimeError"


def test_query_move_for_player_pauses_after_query() -> None:
    calls: list[tuple[str, int]] = []
    engine = GameEngine.__new__(GameEngine)
    engine._cumulative_cpu_usage_usec = {3: 0}
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
        get_cpu_usage_usec=lambda player_id: (
            calls.append(("cpu", player_id)) or (100 if len(calls) == 2 else 130)
        ),
        resume_player=lambda player_id: calls.append(("resume", player_id)),
        pause_player=lambda player_id: calls.append(("pause", player_id)),
    )

    result = GameEngine._query_move_for_player(engine, 3)

    assert result == "move"
    assert calls == [("resume", 3), ("cpu", 3), ("query", 3), ("pause", 3), ("cpu", 3)]
    assert engine._cumulative_cpu_usage_usec == {3: 30}


def test_query_move_for_player_pauses_after_exception() -> None:
    calls: list[tuple[str, int]] = []
    engine = GameEngine.__new__(GameEngine)
    engine._cumulative_cpu_usage_usec = {4: 0}

    def raise_error(*_) -> None:
        calls.append(("query", 4))
        raise RuntimeError("boom")

    engine.state = SimpleNamespace(
        players={4: SimpleNamespace(connection=SimpleNamespace(query_move_player=raise_error))}
    )
    engine.validator = object()
    engine.censor = object()
    engine.process_groups = SimpleNamespace(
        get_cpu_usage_usec=lambda player_id: calls.append(("cpu", player_id)) or 100,
        resume_player=lambda player_id: calls.append(("resume", player_id)),
        pause_player=lambda player_id: calls.append(("pause", player_id)),
    )

    try:
        GameEngine._query_move_for_player(engine, 4)
    except RuntimeError as error:
        assert str(error) == "boom"
    else:
        assert False, "expected RuntimeError"

    assert calls == [("resume", 4), ("cpu", 4), ("query", 4), ("pause", 4)]


def test_query_move_for_player_pauses_after_cpu_sampling_error() -> None:
    calls: list[tuple[str, int]] = []
    engine = GameEngine.__new__(GameEngine)
    engine._cumulative_cpu_usage_usec = {6: 0}
    engine.state = SimpleNamespace(
        players={
            6: SimpleNamespace(
                connection=SimpleNamespace(query_move_player=lambda state, validator, censor: "move")
            )
        }
    )
    engine.validator = object()
    engine.censor = object()

    def raise_cpu_error(player_id: int) -> int:
        calls.append(("cpu", player_id))
        raise RuntimeError("cpu unavailable")

    engine.process_groups = SimpleNamespace(
        get_cpu_usage_usec=raise_cpu_error,
        resume_player=lambda player_id: calls.append(("resume", player_id)),
        pause_player=lambda player_id: calls.append(("pause", player_id)),
    )

    try:
        GameEngine._query_move_for_player(engine, 6)
    except RuntimeError as error:
        assert str(error) == "cpu unavailable"
    else:
        assert False, "expected RuntimeError"

    assert calls == [("resume", 6), ("cpu", 6), ("pause", 6)]


def test_query_move_for_player_bans_on_cumulative_cpu_usage() -> None:
    engine = GameEngine.__new__(GameEngine)
    engine._cumulative_cpu_usage_usec = {5: 7_900_000}
    engine.state = SimpleNamespace(
        players={
            5: SimpleNamespace(
                connection=SimpleNamespace(
                    query_move_player=lambda state, validator, censor: "move"
                )
            )
        }
    )
    engine.validator = object()
    engine.censor = object()

    cpu_readings = iter([100, 250_101])
    engine.process_groups = SimpleNamespace(
        get_cpu_usage_usec=lambda player_id: next(cpu_readings),
        resume_player=lambda player_id: None,
        pause_player=lambda player_id: None,
    )

    try:
        GameEngine._query_move_for_player(engine, 5)
    except Exception as error:
        assert error.__class__.__name__ == "CumulativeTimeoutException"
        assert "cumulative CPU time limit" in str(error)
    else:
        assert False, "expected cumulative timeout"
