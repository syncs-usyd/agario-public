import sys

from engine.game_engine import GameEngine


def main() -> None:
    game = GameEngine(len(sys.argv) > 1 and sys.argv[1] == "--print-recording-interactive")
    game.start()


if __name__ == "__main__":
    main()
