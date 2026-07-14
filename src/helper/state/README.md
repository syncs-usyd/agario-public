Client state is not the authoritative state: the engine side is. These state objects update through the public models and query payloads, not by direct access to engine internals.

If you are trying to work out what a bot can actually read, start with:

- `../game.py`
- `../../lib/interface/queries/query_move.py`
- `../../engine/interface/io/censor_event.py`

Two easy-to-miss details:

- `game.state.map` is only a size view. Use `game.state.map.size` or `game.state.map_size`; it does not expose foods, viruses, or spawn helpers.
- `ClientPlayer.round_died` exists on the helper object but is not currently updated by the helper mutator.
- `game.state.rankings` is updated from the engine query each tick and is ordered by descending total mass.
