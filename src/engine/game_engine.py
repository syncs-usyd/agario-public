from time import perf_counter, sleep

from lib.config.arena import NUM_PLAYERS, MAX_ROUNDS, TURN_DURATION_SECONDS, VISION_SIZE
from engine.interface.io.censor_event import CensorEvent
from engine.interface.io.exceptions import PlayerException
from engine.interface.io.game_result import (
    GameBanResult,
    GameCancelledResult,
    GameSuccessResult,
)
from engine.interface.io.input_validator import MoveValidator
from engine.interface.logging.event_factory import event_banned_factory
from engine.interface.logging.event_inspector import EventInspector
from engine.state.game_state import GameState
from engine.config.io_config import CORE_DIRECTORY

from engine.state.state_mutator import StateMutator

from lib.interface.events.event_food_spawned import EventFoodSpawned
from lib.interface.events.event_player_won import EventPlayerWon
from lib.interface.events.event_game_started import EventGameStarted
from lib.interface.events.moves.move_player import MovePlayer

from random import sample
import shutil


class GameEngine:
    def __init__(self, print_recording_interactive: bool = False) -> None:
        print("Intialising game engine!")

        self.state = GameState()
        self.validator = MoveValidator(self.state)
        self.mutator = StateMutator(self.state)
        self.censor = CensorEvent(self.state)

    def start(self) -> None:
        try:
            self.state._connect_players()
            self.run_game()
        except PlayerException as e:
            event = event_banned_factory(e)
            self.mutator.commit(event)
        finally:
            self.finish()

    def run_game(self) -> None:
        assert NUM_PLAYERS == len(self.state.players)
        turn_order = sample(list(self.state.players.keys()), k=NUM_PLAYERS)
        self.state.turn_order = turn_order

        self.mutator.commit(
            EventGameStarted(
                turn_order=self.state.turn_order,
                arena_size=self.state.map.size,
                vision_size=VISION_SIZE,
                turn_duration_seconds=TURN_DURATION_SECONDS,
                max_rounds=MAX_ROUNDS,
                players=[
                    player._to_model()
                    for player in self.state.players.values()
                ],
            )
        )
        self.mutator.commitPrivate(EventFoodSpawned(foods=list(self.state.map.foods)))

        while not self.state.is_game_over():
            print(f"New round {self.state.round + 1}", flush=True)
            round_started_at = perf_counter()
            self.state.round += 1

            moves: list[MovePlayer] = []
            for player_id in turn_order:
                player = self.state.players[player_id]
                if player.alive:
                    response = player.connection.query_move_player(
                        self.state,
                        self.validator,
                        self.censor,
                    )
                    moves.append(response)
            self.mutator.commit_round(moves)

            remaining = TURN_DURATION_SECONDS - (perf_counter() - round_started_at)
            if remaining > 0:
                sleep(remaining)

        rankings = self.state.get_rankings()
        self.mutator.commit(EventPlayerWon(player_id=rankings[0]))

    def finish(self) -> None:
        # Write the result.
        inspector = EventInspector(
            self.state.private_event_history,
            self.state.get_rankings(),
        )
        result = inspector.get_result()

        with open(f"{CORE_DIRECTORY}/output/results.json", "w") as f:
            f.write(result.model_dump_json())

        # Write the game log.
        with open(f"{CORE_DIRECTORY}/output/game.json", "w") as f:
            f.write(inspector.get_recording_json())

        visualiser_data = inspector.get_visualiser_json()
        with open(
            f"{CORE_DIRECTORY}/output/visualiser_forwards_differential.json", "w"
        ) as f:
            f.write(visualiser_data)

        def copy_stdout_stderr_player(player: int) -> None:
            stderr_path = f"{CORE_DIRECTORY}/submission{player}/io/submission.err"
            stderr_path_new = f"{CORE_DIRECTORY}/output/submission_{player}.err"
            stdout_path = f"{CORE_DIRECTORY}/submission{player}/io/submission.log"
            stdout_path_new = f"{CORE_DIRECTORY}/output/submission_{player}.log"

            try:
                shutil.copy(stderr_path, stderr_path_new, follow_symlinks=False)
            except (FileNotFoundError, IsADirectoryError, FileExistsError):
                with open(stderr_path_new, "w") as f:
                    f.write(
                        "Your submission.err file is either missing or is a directory."
                    )

            try:
                shutil.copy(stdout_path, stdout_path_new, follow_symlinks=False)
            except (FileNotFoundError, IsADirectoryError, FileExistsError):
                with open(stdout_path_new, "w") as f:
                    f.write(
                        "Your submission.log file is either missing or is a directory."
                    )

        # Only copy for the player who was banned, otherwise copy for all players, or only copy the log
        # if the match was cancelled.
        print(f"[engine]: match complete, outcome was {{{result}}}", flush=True)
        match result:
            case GameBanResult() as x:
                copy_stdout_stderr_player(player=x.player)

            case GameSuccessResult():
                for player in self.state.players.keys():
                    copy_stdout_stderr_player(player)

            case GameCancelledResult():
                pass
