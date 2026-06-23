---
name: code-quality
description: Use when formatting, linting, type checking, or reviewing code quality in the GAC project. Covers ruff, mypy, Makefile targets, and coding standards.
tags: [linting, formatting, type-checking, code-standards]
---

# Code Quality Tools and Standards

## When to Use

- Formatting code before committing
- Linting code for errors and style issues
- Type checking for correctness
- Reviewing or refactoring code

## Makefile Targets (canonical)

`make lint` and `make format` run **four tools**, not just ruff:

```bash
make format     # ruff check --fix + ruff format + prettier --write + markdownlint --fix
make lint       # ruff check + ruff format --check + prettier --check + markdownlint --check
make type-check # mypy
make test       # uv run -- pytest
```

Running `uv run ruff check .` alone does NOT equal `make lint`. CI runs all four.

## Individual Tools

```bash
uv run ruff check src/           # Lint
uv run ruff format src/          # Format
uv run mypy src/                 # Type check
```

## Coding Standards

### Type Annotations (required)

```python
def parse_response(response: dict[str, Any]) -> str | None:
    """Parse API response and extract content."""
    message = response.get("message", {})
    return message.get("content")
```

### Naming

- Modules/functions: `snake_case`
- Classes: `CapWords`
- Constants: `UPPER_SNAKE_CASE`

### Line Length: 120 characters max

### Docstrings: Google-style

```python
def generate(model: str, messages: list[dict]) -> tuple[str, int, int, int, int]:
    """Generate text using the AI provider.

    Args:
        model: Model name to use.
        messages: List of message dictionaries.

    Returns:
        Tuple of (content, input_tokens, output_tokens, input_cost, output_cost).
    """
```

### File Size: 600 lines max

Split when exceeded — but don't split purely for line count if it hurts cohesion.

## Pre-commit Workflow

```bash
# 1. Make changes
# 2. Format + lint
make format
make lint
# 3. Type check
make type-check
# 4. Test
make test
# 5. Commit with gac (scope + yes)
gac -sy
```

Note: `-s` is `--scope` (infers commit scope), `-y` is `--yes` (skips confirmation). Not "short mode".

## Checklist

```
[ ] make format run?
[ ] make lint passes? (all 4 tools)
[ ] make type-check passes?
[ ] make test passes?
[ ] File length under 600 lines?
[ ] Type annotations on all functions?
[ ] Docstrings on public functions?
```
