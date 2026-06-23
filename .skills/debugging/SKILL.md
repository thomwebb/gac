---
name: debugging
description: Use when debugging test failures, runtime errors, or unexpected behavior in the GAC project. Covers pytest debugging, logging, and common patterns.
tags: [debugging, troubleshooting, logs]
---

# Debugging Workflows

## When to Use

- Tests are failing and you need to understand why
- Runtime errors occur in CLI operation
- Provider responses are unexpected
- Need to trace code execution flow

## Test Debugging

```bash
uv run -- pytest tests/test_cli.py -v       # Verbose
uv run -- pytest tests/test_cli.py -vv      # Extra verbose
uv run -- pytest tests/test_cli.py -s       # Show print statements
uv run -- pytest tests/test_cli.py -x       # Stop on first failure
uv run -- pytest tests/test_cli.py --pdb    # Debugger on failure
uv run -- pytest tests/test_cli.py --tb=long    # Full traceback
uv run -- pytest tests/test_cli.py --showlocals  # Local variables
```

### Provider Test Debugging

```bash
# Run specific mocked test
uv run -- pytest tests/providers/test_openai.py::TestOpenAIProviderMocked::test_successful_api_call -vvv

# API key validation tests
uv run -- pytest tests/providers/test_openai.py -k "APIKey" -v
```

Note: The standard mocked test is `test_successful_api_call` (NOT `test_successful_call`).

## CLI Debugging

```bash
# Dry run with verbose
gac --dry-run -v

# Message only (no commit)
gac --dry-run --message-only

# Show the prompt sent to LLM
gac --show-prompt --dry-run

# Enable debug logging
GAC_LOG_LEVEL=DEBUG uv run python -m gac.cli --dry-run -v

# Or via CLI flag
uv run python -m gac.cli --log-level DEBUG --dry-run
```

Note: There is NO `GAC_DEBUG` env var. Use `GAC_LOG_LEVEL=DEBUG` or `--log-level DEBUG`.

## Checking Configuration

```bash
# Check which model/provider is configured
uv run python -c "import os; print({k:v for k,v in os.environ.items() if k.startswith('GAC_')})"

# Check stats file location
uv run python -c "from gac.stats.store import STATS_FILE; print(STATS_FILE)"

# Check OAuth token storage
uv run python -c "from gac.oauth.token_store import TOKEN_DIR; print(TOKEN_DIR)"
```

## Stats Debugging (safe)

Always mock stats paths when debugging outside pytest:

```python
from unittest.mock import patch
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmpdir:
    with patch("gac.stats.store.STATS_FILE", Path(tmpdir) / "debug.json"):
        from gac.stats import save_stats
        save_stats({"model": "test"})  # safe — writes to temp
```

## Using pdb

```python
import pdb; pdb.set_trace()  # Breakpoint

# Conditional
if data.get("error"):
    import pdb; pdb.set_trace()
```

Remove debug breakpoints before committing.

## Logging in Code

Use `logging`, not `print()`:

```python
import logging
logger = logging.getLogger(__name__)

def parse_response(response: dict[str, Any]) -> str:
    logger.debug("Received response keys: %s", list(response.keys()))
    return response.get("message", {}).get("content", "")
```

Enable HTTP debugging for provider issues:

```bash
GAC_LOG_LEVEL=DEBUG uv run -- pytest tests/providers/test_openai.py -vv -s
```

## Checklist

```
[ ] Using -v / -s / --pdb for test debugging?
[ ] Using GAC_LOG_LEVEL=DEBUG (not GAC_DEBUG)?
[ ] Mocking stats paths outside pytest?
[ ] Removing debug code before committing?
[ ] Provider test name is test_successful_api_call?
```
