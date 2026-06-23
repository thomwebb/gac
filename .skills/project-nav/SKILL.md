---
name: project-nav
description: Use when navigating the GAC codebase, finding where code lives, or understanding the project structure. 106 source files, 151 test files.
tags: [navigation, project-structure, codebase]
---

# Project Navigation

## When to Use

- Finding where specific code lives
- Understanding project structure
- Locating configuration files
- Looking for where to add new features

## Structure (106 source files)

```
gac/
  src/gac/
    cli.py                   # Click CLI entrypoint
    main.py                  # Commit workflow orchestration
    ai.py / ai_utils.py      # AI provider integration + retry logic
    prompt.py / prompt_builder.py  # Dual-prompt system
    git.py                   # Git operations
    security.py              # Secret detection
    config.py                # Config loading (GACConfig TypedDict)
    errors.py                # Exception hierarchy (GACError base)
    preprocess.py / postprocess.py  # Diff preprocessing / message cleanup
    diff_scoring.py          # Diff relevance scoring

    providers/               # 35 provider implementations
      __init__.py            # PROVIDER_REGISTRY
      base.py                # BaseConfiguredProvider, OpenAICompatibleProvider,
                             #   AnthropicCompatibleProvider, GenericHTTPProvider
      error_handler.py       # @handle_provider_errors decorator
      protocol.py            # ProviderProtocol
      registry.py            # register_provider()
      openai.py, anthropic.py, gemini.py, ...

    oauth/                   # OAuth authentication
      base.py                # Base OAuth flow (19KB)
      chatgpt.py             # ChatGPT OAuth
      claude_code.py         # Claude Code OAuth
      copilot.py             # GitHub Copilot OAuth
      token_store.py         # Token storage (~/.gac/oauth/)

    stats/                   # Statistics tracking
      store.py               # Stats file read/write
      recorder.py            # Usage recording
      commands.py            # Stats CLI commands
      charts.py              # Chart generation
      summary.py             # Summary formatting
      migration.py           # Legacy migration

    mcp/                     # MCP server
      server.py              # MCP server implementation (22KB)
      server_utils.py        # Server utilities
      models.py              # MCP data models

    constants/               # Constants package
      defaults.py            # EnvDefaults, etc.
      commit.py              # Commit format constants
      file_patterns.py       # Secret detection patterns
      languages.py           # Language code mappings

    grouped_commit_*.py      # Grouped commit workflow (5 files)
    *_cli.py                 # Subcommand CLIs (config, init, diff, model, etc.)
    workflow_context.py      # WorkflowContext dataclass

  tests/                     # 151 test files mirroring src/
  docs/                      # Documentation (16 languages)
  scripts/                   # Automation helpers
```

This is not exhaustive. Use `find src/gac -name "*.py"` to explore.

## Finding Code

Use system tools directly (NOT `uv run` — these aren't Python packages):

```bash
rg "def generate" src/gac/                    # ripgrep for definitions
rg "class.*Provider" src/gac/providers/       # Find provider classes
rg "os.getenv" src/gac/                       # Find env var usage
ls src/gac/providers/*.py | grep -v __init__  # List providers
```

## Source to Test Mapping

Tests mirror source but may be split across multiple files:

| Source                        | Tests                                                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `src/gac/cli.py`              | `tests/test_cli.py`                                                                                          |
| `src/gac/git.py`              | `tests/test_git.py`, `tests/test_git_coverage.py`, `tests/test_git_integration.py`                           |
| `src/gac/stats/store.py`      | `tests/test_stats_core.py`, `tests/test_stats_tracking.py`, `tests/test_stats_malformed.py`, ... (15+ files) |
| `src/gac/providers/openai.py` | `tests/providers/test_openai.py`                                                                             |
| `src/gac/mcp/server.py`       | `tests/test_mcp_server.py`, `tests/test_mcp_utils.py`                                                        |

## Key Entry Points

| Starting from      | Read first                                                            |
| ------------------ | --------------------------------------------------------------------- |
| CLI flags          | `src/gac/cli.py` — Click `@click.option` decorators                   |
| Commit workflow    | `src/gac/main.py` — `generate_commit_message()`                       |
| Provider internals | `src/gac/providers/base.py:188` — `BaseConfiguredProvider.generate()` |
| Config values      | `src/gac/config.py` — `GACConfig` TypedDict + `load_config()`         |
| Error types        | `src/gac/errors.py` — `GACError` base, `AIError`, `SecurityError`     |

## Navigation Tips

- Provider registry: `from gac.providers import PROVIDER_REGISTRY`
- Config: `from gac.config import load_config`
- Provider method is `generate()`, returns tuple `(content, in_tok, out_tok, in_cost, out_cost)`
- NEVER edit `~/.gac*` files during development
