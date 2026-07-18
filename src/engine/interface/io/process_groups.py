import json
import os

from signal import SIGCONT, SIGSTOP, Signals
from typing import Iterable

from engine.config.io_config import CORE_DIRECTORY

PROCESS_GROUPS_FILENAME = "submission_process_groups.json"


class ProcessGroupController:
    def __init__(self, process_groups: dict[int, int] | None = None) -> None:
        self._process_groups = process_groups if process_groups is not None else {}

    @classmethod
    def from_core_directory(
        cls, core_directory: str = CORE_DIRECTORY
    ) -> "ProcessGroupController":
        path = os.path.join(core_directory, PROCESS_GROUPS_FILENAME)
        try:
            with open(path, "r") as process_groups_file:
                data = json.load(process_groups_file)
        except (FileNotFoundError, NotADirectoryError, json.JSONDecodeError):
            return cls()

        if not isinstance(data, list):
            return cls()

        process_groups: dict[int, int] = {}
        for entry in data:
            if not isinstance(entry, dict):
                continue
            player_id = entry.get("player_id")
            pgid = entry.get("pgid")
            if isinstance(player_id, int) and isinstance(pgid, int):
                process_groups[player_id] = pgid

        return cls(process_groups)

    def pause_player(self, player_id: int) -> None:
        self._signal_player(player_id, SIGSTOP)

    def resume_player(self, player_id: int) -> None:
        self._signal_player(player_id, SIGCONT)

    def pause_all(self) -> None:
        self._signal_process_groups(self._process_groups.values(), SIGSTOP)

    def _signal_player(self, player_id: int, signal: Signals) -> None:
        pgid = self._process_groups.get(player_id)
        if pgid is None:
            return
        self._signal_process_groups([pgid], signal)

    @staticmethod
    def _signal_process_groups(process_groups: Iterable[int], signal: Signals) -> None:
        for pgid in dict.fromkeys(process_groups):
            try:
                os.killpg(pgid, signal)
            except ProcessLookupError:
                continue
