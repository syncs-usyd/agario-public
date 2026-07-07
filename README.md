# agario-public

Public source repository for the Agar.io bot competition.

This repo publishes a single Python package:

- `agario-kit`

That one distribution contains the modules competitors and private
infrastructure use:

- `lib`: shared models, config, and protocol types
- `helper`: helper API that student bots import
- `engine`: the authoritative game engine
- `agario_visualiser`: local match launcher and first-person visualiser

## Layout

```text
src/
  agario_kit/
  agario_visualiser/
  engine/
  helper/
  lib/
examples/
  submissions/
docs/
tests/
```

## If you are writing a bot

If you are trying to work out what data a bot can actually read at runtime, start with:

- `src/helper/game.py`
- `src/lib/interface/queries/query_move.py`
- `src/engine/interface/io/player_connection.py`
- `src/engine/interface/io/censor_event.py`

## Local development

```bash
uv sync
uv run pytest
uv run interactive 2:examples/submissions/cautious.py 1:examples/submissions/dont_move.py
uv run simulation 3:examples/submissions/cautious.py 1:examples/submissions/dont_move.py
```
