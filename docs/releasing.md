# Releasing `agario-public`

## What gets published

This repository builds and publishes one Python distribution package:

- `agario-kit`

That single distribution contains the runtime modules competitors and private
infrastructure use:

- `lib`
- `helper`
- `engine`
- `agario_visualiser`

## GitHub Actions

- `.github/workflows/ci.yml` runs tests on pushes to `main` and on pull requests.
- `.github/workflows/publish.yml`:
  - publishes to PyPI on git tags matching `v*`
  - can publish to TestPyPI manually via `workflow_dispatch`

The publish workflow builds the distribution into `dist/`, checks it with
`twine check`, then uploads them through `pypa/gh-action-pypi-publish`.

## Trusted Publishing setup

Configure the GitHub workflow as a Trusted Publisher for the `agario-kit`
project on both PyPI and TestPyPI.

Use these values when configuring each publisher:

- Repository owner: your GitHub org or username
- Repository name: `agario-public`
- Workflow filename: `publish.yml`
- GitHub environment:
  - `pypi` for PyPI
  - `testpypi` for TestPyPI

## Release steps

1. Update the version in the root `pyproject.toml`.
2. Commit and push to `main`.
5. Create and push a tag such as `v2026.1.1` <- same tag as what you updated it to.
7. Announce the release to competitors:

```bash
uv lock --upgrade-package agario-kit==2026.1.1
uv sync
```

## Competitor install target

Competitors install only this package:

```bash
uv add agario-kit==2026.1.1
```
