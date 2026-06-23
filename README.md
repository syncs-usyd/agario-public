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

## Local development

```bash
uv sync
uv run pytest
uv run agario-local-match --submission examples/submissions/bot_1.py --submission examples/submissions/bot_2.py --submission examples/submissions/aggressive.py --masquerade
```
