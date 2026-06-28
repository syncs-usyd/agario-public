# Release Notes

To publish a new `agario-kit` version:

1. Update the version in `pyproject.toml`.
2. Commit and push `main`.
3. Tag the release and push the tag.

Example for `2026.1.1`:

```bash
git add .
git commit -m "Rename public commands and bump to 2026.1.1"
git push origin main
git tag v2026.1.1
git push origin v2026.1.1
```
