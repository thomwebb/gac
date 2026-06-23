# GAC — Agent Guidelines

Essential rules for AI coding agents. Detailed reference: load skills from `.skills/`.

## uv run (NON-NEGOTIABLE)

Every Python command must go through `uv run`:

| Always                    | Never              |
| ------------------------- | ------------------ |
| `uv run pytest`           | `pytest`           |
| `uv run python script.py` | `python script.py` |
| `uv run ruff check .`     | `ruff check .`     |
| `uv run mypy src/`        | `mypy src/`        |
| `uv run pip install X`    | `pip install X`    |

This project has 35+ AI provider integrations — only `uv` + `uv.lock` can resolve the dependency matrix reliably across dev, CI, and production. Vanilla tools will silently break.

**For subagents:** always include `uv run` in prompts you generate. Verify compliance before accepting output.

## User Data Safety (NON-NEGOTIABLE)

NEVER touch `~/.gac*` files during development or testing:

- `~/.gac/stats.json`, `~/.gac_stats.json` (legacy, auto-migrated)
- `~/.gac.env`, `~/.gac/oauth/*.json`

When testing code that touches stats:

```python
#  Use tmp_path + mock the file path
with patch("gac.stats.store.STATS_FILE", tmp_path / "test.json"):
    save_stats(data)  # safe

#  NEVER call reset_stats() / save_stats() without mocking
```

The session-scoped `isolate_stats_file` fixture (`tests/conftest.py`) handles this automatically **inside pytest only**. Outside pytest, back up first: `cp ~/.gac/stats.json{,.bak}`.

Accidental data loss is unacceptable.

## Commands

```bash
make setup              # uv venv && uv pip install -e ".[dev]"
make test               # uv run -- pytest (excludes integration)
make test-integration   # real API calls (needs API keys)
make test-cov           # coverage report → htmlcov/index.html
make lint               # ruff check + ruff format --check + prettier + markdownlint (4 tools!)
make format             # auto-fix all four
make type-check         # mypy
```

Run specific tests:

```bash
uv run -- pytest tests/test_cli.py                    # single file
uv run -- pytest tests/providers/test_openai.py -v    # verbose
uv run -- pytest -k "test_parse_response"             # by name
```

## Commits

- **Use `gac -sy`** (scope + yes). Never raw `git commit`.
- Format: Conventional Commits — `feat(ai):`, `fix(providers):`, `docs:`
- NEVER manually edit `CHANGELOG.md` or `__version__.py` — auto-managed.

## Coding Standards

- Python 3.10+, type annotations required
- Ruff formatter, 120-char lines
- `snake_case` for modules/functions, `CapWords` for classes
- Files under 600 lines (split when exceeded)

## Architecture (brief)

- **Entry point**: `src/gac/cli.py` (Click CLI) → `src/gac/main.py` (workflow orchestration)
- **Providers**: 35+ in `src/gac/providers/`, all extend `BaseConfiguredProvider`
  - Base classes: `OpenAICompatibleProvider`, `AnthropicCompatibleProvider`, `GenericHTTPProvider`
  - Provider method is **`generate()`**, NOT `complete()`
  - Registry: `src/gac/providers/__init__.py` → `PROVIDER_REGISTRY`
- **Subsystems**: `oauth/` (5 files), `stats/` (6 files), `mcp/` (3 files), `constants/` (4 files), `grouped_commit_*.py` (5 files)
- **Tests**: 151 files mirroring `src/` structure
- **Prompt system**: dual-prompt tuple `(system_prompt, user_prompt)` in `prompt.py` / `prompt_builder.py`
- **Config**: environment variables + `~/.gac.env` → `src/gac/config.py` → `GACConfig` TypedDict

## Installation Types

- **Development** (project venv only): `uv pip install -e ".[dev]"` — editable, changes reflected immediately
- **Stable** (outside venv): `pipx install` — never use `-e` flag outside project venv
