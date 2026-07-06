Client state is not the authoritative state: the engine side is. These state objects update through the public models and query payloads, not by direct access to engine internals.

If you are trying to work out what a bot can actually read, start with:

- `../../../docs/bot-runtime-surface.md`
- `../game.py`
- `../../lib/interface/queries/query_move.py`
- `../../engine/interface/io/censor_event.py`

Two easy-to-miss details:

- `game.state.map.size` is synced, but `game.state.map.foods` and `game.state.map.viruses` are not.
- `ClientPlayer.round_died` exists on the helper object but is not currently updated by the helper mutator.
