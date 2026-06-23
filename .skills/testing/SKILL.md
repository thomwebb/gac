---
name: testing
description: Use when running, writing, or debugging tests in the GAC project. Covers test structure, pytest commands, provider testing patterns, and integration vs unit test practices.
tags: [testing, pytest, test-structure, integration]
---

# Testing Workflows

## When to Use

- Running tests (entire suite or specific tests)
- Writing new tests or modifying existing ones
- Debugging test failures
- Understanding provider test patterns

## Test Structure

The suite has **151 test files** mirroring `src/`. Key areas:

```
tests/
  conftest.py                 # Shared fixtures (isolate_stats_file, etc.)
  test_cli.py                 # CLI tests
  test_main.py                # Workflow orchestration
  test_config.py              # Config loading/validation
  test_ai.py                  # AI integration (registry tests)
  providers/                  # 35+ provider test files
    conftest.py               # BaseProviderTest + fixtures
    test_openai.py
    test_anthropic.py
    ...
  oauth/                      # 7 OAuth flow test files
  test_mcp_server.py          # MCP server tests
  test_grouped_*.py           # 10+ grouped commit workflow tests
  test_stats_*.py             # 15+ stats tests (core, cli, charts, migration, etc.)
  test_interactive_mode_*.py  # Interactive mode tests
```

This is not exhaustive. Use `ls tests/` to explore.

## Commands

```bash
uv run -- pytest              # All tests (excludes integration)
uv run -- pytest -x           # Stop on first failure
uv run -- pytest -v           # Verbose output
uv run -- pytest tests/test_cli.py              # Single file
uv run -- pytest -k "test_parse_response"       # By name pattern
uv run -- pytest --pdb                          # Debugger on failure
uv run -- pytest -s                             # Show print statements
```

Integration tests (need API keys):

```bash
make test-integration         # or: uv run -- pytest -m integration
```

## Provider Test Structure

Each provider has three test types. See `tests/providers/conftest.py` for `BaseProviderTest`.

### 1. Unit Tests — no external dependencies

```python
class TestOpenAIImports:
    def test_import_module(self):
        from gac.providers import openai
        assert openai is not None

    def test_provider_in_registry(self):
        from gac.providers import PROVIDER_REGISTRY
        assert "openai" in PROVIDER_REGISTRY
```

### 2. Mocked Tests — inherit from BaseProviderTest (9 standard tests)

```python
class TestOpenAIProviderMocked(BaseProviderTest):
    # Inherits: test_successful_api_call, test_empty_content_handling,
    # test_http_401_authentication_error, test_http_429_rate_limit_error,
    # test_http_500_server_error, test_http_503_service_unavailable,
    # test_connection_error, test_timeout_error, test_malformed_json_response
```

### 3. Integration Tests — real API calls

```python
@pytest.mark.integration
def test_real_api_call():
    provider = OpenAIProvider(config=ProviderConfig(...))
    content, in_tok, out_tok, cost_in, cost_out = provider.generate(
        model="gpt-4",
        messages=[{"role": "user", "content": "test"}],
    )
    assert content is not None
```

Note: `generate()` returns a **tuple** `(content, input_tokens, output_tokens, input_cost, output_cost)`.

## Writing New Tests

### File Placement

Tests mirror source:

- `src/gac/git.py` -> `tests/test_git.py`
- `src/gac/providers/openai.py` -> `tests/providers/test_openai.py`

### Naming

```python
def test_<function>_<scenario>():
    """Test <function> in <scenario> situation."""
```

### Stats Safety

The session-scoped `isolate_stats_file` fixture redirects stats files to temp dirs. It is active **in pytest only**. If running outside pytest, mock manually:

```python
with patch("gac.stats.store.STATS_FILE", tmp_path / "test.json"):
    save_stats({"model": "test"})  # safe
```

See AGENTS.md for full user data safety rules.

## Coverage

```bash
make test-cov                 # Matches CI: --cov=src --cov-report=term --cov-report=html
open htmlcov/index.html
```

## Checklist

```
[ ] Using uv run -- pytest prefix?
[ ] Tests mirror source structure?
[ ] Using tmp_path for file operations?
[ ] Mocking httpx in unit tests?
[ ] @pytest.mark.integration for real API calls?
[ ] Provider method is generate(), not complete()
[ ] Test class inherits BaseProviderTest for mocked HTTP tests?
```
