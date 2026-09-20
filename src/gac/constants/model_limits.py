"""Conservative per-provider context window limits.

Used to derive a diff token budget that fits the *configured* model instead
of assuming every provider has a huge context window (issue #79).  Values are
deliberately conservative: they bound the git-diff portion of the prompt, and
underestimating a limit only means slightly earlier truncation, never an API
error.
"""

from gac.constants.defaults import Utility

# Conservative context-window defaults per provider key (tokens).
# Local runtimes (Ollama, LM Studio) default small because model catalogs are
# user-controlled and frequently ship 4k-8k context models.
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
    # Local runtimes — catalogs are user-controlled, assume small windows
    "lm-studio": 8_192,
    "ollama": 8_192,
    # Unknown custom endpoints
    "custom-openai": 32_768,
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

    The budget is the smaller of the configured cap (default
    ``Utility.DEFAULT_DIFF_TOKEN_LIMIT``) and ``_DIFF_BUDGET_FRACTION`` of the
    model's context window, never below ``_MIN_DIFF_BUDGET``.
    """
    cap = configured if configured is not None else Utility.DEFAULT_DIFF_TOKEN_LIMIT
    context_budget = int(resolve_context_limit(model) * _DIFF_BUDGET_FRACTION)
    return max(_MIN_DIFF_BUDGET, min(cap, context_budget))
