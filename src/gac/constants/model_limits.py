"""Per-provider context window assumptions and diff budget resolution.

Used to derive a diff token budget for the *configured* model (issue #79).
Windows are deliberately optimistic: most modern catalogs (cloud and local)
ship 128k+ contexts, and an oversized prompt now fails with a clear,
actionable error (see ``providers/error_handler.py``) rather than silently
degrading.  Users who know their model is smaller can set an explicit cap
via ``GAC_MAX_DIFF_TOKENS``.
"""

from gac.constants.defaults import Utility

# Optimistic context-window defaults per provider key (tokens).
# Local runtimes (Ollama, LM Studio) assume modern defaults — users with
# smaller models can cap explicitly via GAC_MAX_DIFF_TOKENS.
PROVIDER_CONTEXT_LIMITS: dict[str, int] = {
    # OpenAI-compatible frontier hosts
    "openai": 128_000,
    "azure-openai": 128_000,
    "chatgpt-oauth": 128_000,
    "copilot": 128_000,
    # Anthropic
    "anthropic": 200_000,
    "claude-code": 200_000,
    "custom-anthropic": 200_000,
    # Google
    "gemini": 1_000_000,
    # Cloud relays / aggregators (most host >=128k-context catalogs)
    "cerebras": 128_000,
    "chutes": 128_000,
    "crof": 128_000,
    "deepinfra": 128_000,
    "deepseek": 128_000,
    "fireworks": 128_000,
    "groq": 128_000,
    "kimi-coding": 128_000,
    "minimax": 128_000,
    "mistral": 128_000,
    "moonshot": 128_000,
    "neuralwatt": 128_000,
    "ollama-cloud": 128_000,
    "opencode-go": 128_000,
    "openrouter": 128_000,
    "plexus": 128_000,
    "qwen": 128_000,
    "qwen-api": 128_000,
    "qwen-api-cn": 128_000,
    "replicate": 128_000,
    "streamlake": 128_000,
    "synthetic": 128_000,
    "together": 128_000,
    "wafer": 128_000,
    "zai": 128_000,
    "zai-coding": 128_000,
    # Local runtimes and custom endpoints — assume modern default windows
    "lm-studio": 128_000,
    "ollama": 128_000,
    "custom-openai": 128_000,
}

DEFAULT_CONTEXT_LIMIT: int = 32_768

# Fraction of the context window reserved for the diff.  The remainder has to
# cover the system prompt, task instructions, and the generated message.
_DIFF_BUDGET_FRACTION: float = 0.6
_MIN_DIFF_BUDGET: int = 2_048


def resolve_context_limit(model: str) -> int:
    """Return the conservative context window for a ``provider:model`` string.

    Unknown providers fall back to ``DEFAULT_CONTEXT_LIMIT``.
    """
    provider = model.split(":", 1)[0].strip().lower() if model else ""
    return PROVIDER_CONTEXT_LIMITS.get(provider, DEFAULT_CONTEXT_LIMIT)


def resolve_diff_token_limit(model: str, configured: int | None = None) -> int:
    """Derive the git-diff token budget for *model*.

    When *configured* is provided (e.g. ``GAC_MAX_DIFF_TOKENS``), it is used
    directly as the budget — explicit user configuration overrides the
    heuristic entirely.  Otherwise the budget is ``_DIFF_BUDGET_FRACTION``
    of the model's assumed context window, capped at
    ``Utility.DEFAULT_DIFF_TOKEN_LIMIT`` and never below ``_MIN_DIFF_BUDGET``.
    """
    if configured is not None:
        return max(_MIN_DIFF_BUDGET, configured)
    context_budget = int(resolve_context_limit(model) * _DIFF_BUDGET_FRACTION)
    return max(_MIN_DIFF_BUDGET, min(Utility.DEFAULT_DIFF_TOKEN_LIMIT, context_budget))
