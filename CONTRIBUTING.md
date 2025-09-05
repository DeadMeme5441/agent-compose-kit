Contributing
============

Thanks for your interest in contributing! This project is a core library for composing
agent systems using Google ADK, intended to be consumed by external CLIs and services.

Ways to contribute
- Bug reports and feature requests via issues
- Documentation improvements
- Tests and small fixes
- New examples and templates

Development setup
- Install uv (https://docs.astral.sh/uv/)
- Sync dev deps: `uv sync --dev`
- Run tests: `uv run pytest -q`
- Lint/format: `uv run ruff check .` and `uv run ruff format .`

Commit style
- Use Conventional Commits (e.g., `feat: add agent registry`, `fix: resolve tool import error`).
- Include a concise summary, scope (optional), and body when helpful.

Pull requests
- Keep changes focused; add/update tests and docs where appropriate.
- Ensure CI passes (ruff + pytest).
- Link related issues and describe rationale in the PR description.

Release process
- We use SemVer. Bump version via `uv version` and tag releases `vX.Y.Z`.
- Publishing is handled by GitHub Actions on tags. We recommend PyPI Trusted Publisher.

Code of conduct
- Be respectful and inclusive. We aim for a collaborative environment for maintainers
  and contributors alike.

