from lib.interact.map import Map

from collections import defaultdict, deque
from typing import Callable, Iterator, Protocol


class SharedGameState(Protocol):
    map: Map


class GameLogic(SharedGameState):
    pass