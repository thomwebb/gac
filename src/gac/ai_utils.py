"""Utilities for AI provider integration for gac.

This module provides utility functions that support the AI provider implementations.
"""

import logging
import os
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from rich.status import Status

from gac.errors import AIError
from gac.oauth import refresh_token_if_expired
from gac.oauth.token_store import TokenStore
from gac.utils import console

__all__ = [
    "allocate_reasoning_tokens",
    "generate_with_retries",
    "count_tokens",
    "estimate_reasoning_tokens",
    "extract_text_content",
    "normalize_output_tokens",
    "normalize_reasoning_tokens",
    "resolve_reasoning_tokens",
]

logger = logging.getLogger(__name__)


def extract_text_content(content: str | list[dict[str, str]] | dict[str, Any]) -> str:
    """Extract text content from various input formats."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        return "\n".join(
            msg["content"]
            for msg in content
            if isinstance(msg, dict) and "content" in msg and msg["content"] is not None
        )
    elif isinstance(content, dict) and "content" in content:
        return cast(str, content["content"])
    return ""


# ---------------------------------------------------------------------------
# Learned token-per-character ratios
# ---------------------------------------------------------------------------
# When the API reports real prompt_tokens we can compute the actual
# chars-per-token ratio for that model and store it keyed by the bare
# model name (the part after ``:``).  Future ``count_tokens`` calls use the
# stored ratio for that model, falling back to a hardcoded default.
#
# The store is lazily loaded on first access so that tests can set
# ``GAC_TOKEN_RATIOS_PATH`` (or monkeypatch ``_TOKEN_RATIOS_PATH``) before
# the module reads the real home-directory file.

_DEFAULT_RATIO = 3.4

# In-memory cache — populated lazily by ``_ensure_ratios_loaded()``.
_LEARNED_RATIOS: dict[str, float] = {}
_ratios_loaded: bool = False
_ratios_lock = threading.Lock()

# Path to the learned-ratios store.  Overridable via the env var
# ``GAC_TOKEN_RATIOS_PATH`` or, in tests, via ``monkeypatch``.
_TOKEN_RATIOS_PATH: Path = Path(
    os.path.expanduser(os.environ.get("GAC_TOKEN_RATIOS_PATH", str(Path.home() / ".gac/token_ratios.json")))
)


def _ensure_ratios_loaded() -> None:
    """Populate ``_LEARNED_RATIOS`` from disk on first call (idempotent)."""
    global _ratios_loaded
    with _ratios_lock:
        if _ratios_loaded:
            return
        _LEARNED_RATIOS.clear()
        _LEARNED_RATIOS.update(_load_learned_ratios())
        _ratios_loaded = True


# Bounds for chars-per-token ratios.  Real tokenizers produce roughly
# 2–5 chars/token (GPT-4 ~3.5, Claude ~2.8, open-weight models ~3–5).
# Values below 1.5 imply absurdly many tokens per character (a single
# character = multiple tokens).  Values above 6.0 imply absurdly few
# tokens per character (nearly one token per character), which is
# impossible for real tokenizers.  We clamp to [1.5, 6.0] so that a
# poison value (e.g. 95.0 from a corrupted file) cannot silently
# collapse token estimates to near-zero.
_MIN_RATIO = 1.5
_MAX_RATIO = 6.0


def _load_learned_ratios() -> dict[str, float]:
    """Load learned token ratios from the on-disk JSON file.

    Returns an empty dict when the file doesn't exist or is corrupt —
    callers fall back to ``_DEFAULT_RATIO``.

    Each loaded value is clamped to ``[_MIN_RATIO, _MAX_RATIO]`` so that
    poisoned or corrupted values cannot cause token-count collapse.
    """
    import json

    try:
        if _TOKEN_RATIOS_PATH.is_file():
            data = json.loads(_TOKEN_RATIOS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                clamped: dict[str, float] = {}
                for k, v in data.items():
                    if isinstance(v, (int, float)) and v > 0:
                        clamped[k] = max(_MIN_RATIO, min(_MAX_RATIO, float(v)))
                return clamped
    except (OSError, json.JSONDecodeError, ValueError):
        pass
    return {}


def _save_learned_ratios(ratios: dict[str, float]) -> None:
    """Persist learned token ratios to disk atomically (best-effort, never raises)."""
    import json
    import tempfile

    try:
        # Write to a temporary file in the same directory, then atomically replace.
        # This avoids leaving a partial/corrupt file on crash or concurrent write.
        parent = _TOKEN_RATIOS_PATH.parent
        parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                json.dump(ratios, tmp, indent=2)
            os.replace(tmp_name, str(_TOKEN_RATIOS_PATH))
        except OSError:
            # Clean up temp file if replace failed
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
    except OSError:
        pass  # Silently ignore write failures (permissions, disk full, etc.)


def _record_token_ratio(model: str, char_count: int, token_count: int) -> None:
    """Record an observed chars-per-token ratio for *model*.

    Called after a successful API response where we know both the input
    character count and the actual prompt token count.  Stores a running
    average keyed by the bare model name (the part after ``:``) so that
    the same model accessed through different providers shares the estimate.
    """
    if char_count <= 0 or token_count <= 0:
        return

    # Extract bare model name: "wafer:glm5.1" → "glm5.1", "gpt-4o" stays "gpt-4o"
    model_name = model.split(":", 1)[1] if ":" in model else model

    _ensure_ratios_loaded()

    new_ratio = char_count / token_count
    # Clamp to plausible bounds (see _MIN_RATIO / _MAX_RATIO above).
    new_ratio = max(_MIN_RATIO, min(_MAX_RATIO, new_ratio))

    # Running average: weight the new observation at 30% so the estimate
    # adapts to the real tokenizer without swinging on every call.
    with _ratios_lock:
        old = _LEARNED_RATIOS.get(model_name)
        if old is not None:
            blended = 0.7 * old + 0.3 * new_ratio
        else:
            blended = new_ratio
        _LEARNED_RATIOS[model_name] = round(blended, 4)
        _save_learned_ratios(_LEARNED_RATIOS)


# ---- public API ----


def count_tokens(content: str | list[dict[str, str]] | dict[str, Any], model: str) -> int:
    """Count tokens using a character-based heuristic.

    If we have a *learned* chars-per-token ratio for *model* (exact match
    first, then bare model-name fallback), use it.  Otherwise fall back to
    ``_DEFAULT_RATIO`` (3.4).

    Args:
        content: The text or message list to count tokens for.
        model: Model identifier string (e.g. "wafer:glm5.1", "anthropic:claude-sonnet",
               or bare "glm5.1" — all resolve to the same key).

    Returns:
        Estimated token count (always >= 1 for non-empty input).
    """
    _ensure_ratios_loaded()

    text = extract_text_content(content)
    if not text:
        return 0

    # Look up by bare model name (strip provider prefix if present).
    model_name = model.split(":", 1)[1] if ":" in model else model
    raw_ratio = _LEARNED_RATIOS.get(model_name, _DEFAULT_RATIO)
    # Clamp the in-memory value too, so a poisoned entry that somehow
    # bypassed _load_learned_ratios still cannot produce absurd results.
    ratio = max(_MIN_RATIO, min(_MAX_RATIO, raw_ratio))

    result = round(len(text) / ratio)
    return result if result > 0 else 1


def estimate_reasoning_tokens(reasoning_text: str) -> int:
    """Estimate reasoning tokens from the reasoning/thinking content text.

    Uses ``_DEFAULT_RATIO`` (3.4 chars/token).  Returns 0 for empty text.
    (No model-specific ratio yet — call sites don't pass a model identifier
    through to reasoning estimation.)
    """
    if not reasoning_text or not reasoning_text.strip():
        return 0
    result = round(len(reasoning_text) / _DEFAULT_RATIO)
    return result if result > 0 else 1


def allocate_reasoning_tokens(
    completion_tokens: int,
    reasoning_chars: int,
    output_chars: int,
) -> int:
    """Allocate reasoning tokens from completion tokens by character proportion.

    When the API reports ``completion_tokens`` but doesn't break out
    reasoning vs output separately, we split proportionally:
    ``reasoning_tokens = completion_tokens * reasoning_chars / total_chars``.

    This is more accurate than independent estimation (``chars / 3.4``)
    because it uses the real token count from the API, and it's
    self-consistent: ``reasoning_tokens + output_tokens == completion_tokens``.

    Args:
        completion_tokens: Total completion tokens from the API (includes
            both reasoning and output).  Pass ``-1`` if unknown.
        reasoning_chars: Character count of the reasoning/thinking text.
        output_chars: Character count of the output text (excluding reasoning).

    Returns:
        Estimated reasoning token count (0 when no reasoning text).
    """
    if reasoning_chars <= 0:
        return 0
    total_chars = reasoning_chars + output_chars
    if total_chars <= 0:
        return 0
    if completion_tokens >= 0:
        share = reasoning_chars / total_chars
        result = round(completion_tokens * share)
        return result if result > 0 else 1
    # No API token count -- fall back to char-based estimation.
    return estimate_reasoning_tokens("A" * reasoning_chars)


def normalize_output_tokens(completion_tokens: int, reasoning_tokens: int) -> int:
    """Subtract reasoning tokens from completion when the API includes them.

    Some providers use the OpenAI convention where completion_tokens includes
    reasoning; others already exclude it.  When ``completion_tokens <
    reasoning_tokens``, subtraction would produce a negative number, so we
    skip subtraction to avoid a false-zero count.
    """
    if completion_tokens < 0:
        return completion_tokens
    if reasoning_tokens <= 0:
        return completion_tokens
    if completion_tokens >= reasoning_tokens:
        return completion_tokens - reasoning_tokens
    return completion_tokens


def resolve_reasoning_tokens(
    completion_tokens: int,
    api_reasoning_tokens: int | None,
    reasoning_chars: int,
    output_chars: int,
) -> tuple[int, int]:
    """Resolve reasoning and output token counts from API data and char proportions.

    Three-tier resolution:
    1. API reported ``api_reasoning_tokens`` (not None) -> trust it.
    2. No API value but reasoning text exists -> proportional allocation.
    3. No reasoning at all -> (0, completion_tokens).

    Returns:
        (reasoning_tokens, output_tokens) tuple.
    """
    if api_reasoning_tokens is not None:
        final_reasoning = api_reasoning_tokens
        final_output = normalize_output_tokens(completion_tokens, final_reasoning)
    elif reasoning_chars > 0:
        final_reasoning = allocate_reasoning_tokens(completion_tokens, reasoning_chars, output_chars)
        final_output = normalize_output_tokens(completion_tokens, final_reasoning)
    else:
        final_reasoning = 0
        final_output = completion_tokens
    return final_reasoning, final_output


def normalize_reasoning_tokens(explicit_tokens: int | None, reasoning_text: str) -> int:
    """Return reasoning token count, falling back to estimation when unavailable.

    Centralises the policy: if the API reported ``reasoning_tokens`` (even
    as ``0``), trust it.  Otherwise (``None`` sentinel = not reported),
    estimate from the reasoning/thinking text content.

    Args:
        explicit_tokens: The ``reasoning_tokens`` value from the API response,
            or ``None`` if the API did not report it at all.  ``0`` means
            "the API explicitly said zero reasoning tokens".
        reasoning_text: The concatenated reasoning/thinking content text, or
            an empty string if no reasoning content was received.

    Returns:
        Either the explicit token count or the estimated count.
    """
    if explicit_tokens is not None:
        return explicit_tokens
    return estimate_reasoning_tokens(reasoning_text)


def _ensure_oauth_token(provider: str) -> None:
    """Ensure OAuth token is fresh for the given provider.

    Checks token expiry, attempts refresh if needed, and injects the
    access token into the environment so the provider can pick it up.
    Raises AIError if the token cannot be obtained.
    """
    oauth_providers: dict[str, dict[str, str]] = {
        "claude-code": {
            "provider_key": "claude-code",
            "env_var": "CLAUDE_CODE_ACCESS_TOKEN",
            "login_cmd": "gac auth claude-code login",
        },
        "chatgpt-oauth": {
            "provider_key": "chatgpt-oauth",
            "env_var": "CHATGPT_OAUTH_API_KEY",
            "login_cmd": "gac auth chatgpt login",
        },
        "copilot": {
            "provider_key": "copilot",
            "env_var": "COPILOT_OAUTH_TOKEN",
            "login_cmd": "gac auth copilot login",
        },
    }

    if provider not in oauth_providers:
        return

    info = oauth_providers[provider]
    provider_key = info["provider_key"]
    env_var = info["env_var"]
    login_cmd = info["login_cmd"]

    # Provider-specific expiry check and refresh
    token_valid = False
    if provider == "claude-code":
        token_valid = refresh_token_if_expired(quiet=True)
    elif provider == "chatgpt-oauth":
        from gac.oauth.chatgpt import is_token_expired as chatgpt_is_expired
        from gac.oauth.chatgpt import refresh_access_token as chatgpt_refresh

        if chatgpt_is_expired():
            token_valid = chatgpt_refresh() is not None
        else:
            token_valid = True
    elif provider == "copilot":
        from gac.oauth.copilot import refresh_token_if_expired as copilot_refresh

        token_valid = copilot_refresh(quiet=True)

    if not token_valid:
        raise AIError.authentication_error(
            f"{provider} token not found or expired. Please authenticate with '{login_cmd}'."
        )

    # Load the (possibly refreshed) token and set env var
    token_store = TokenStore()
    token_data = token_store.get_token(provider_key)
    if token_data and "access_token" in token_data:
        os.environ[env_var] = token_data["access_token"]
    else:
        raise AIError.authentication_error(f"{provider} token not found. Please authenticate with '{login_cmd}'.")


def generate_with_retries(
    provider_funcs: dict[str, Callable[..., tuple[str, int, int, int, int]]],
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    max_retries: int,
    quiet: bool = False,
    is_group: bool = False,
    skip_success_message: bool = False,
    task_description: str = "commit message",
    reasoning_effort: str | None = None,
) -> tuple[str, int, int, int, int]:
    """Generate content with retry logic using direct API calls."""
    # Parse model string to determine provider and actual model
    if ":" not in model:
        raise AIError.model_error(f"Invalid model format. Expected 'provider:model', got '{model}'")

    provider, model_name = model.split(":", 1)

    # Validate provider
    from gac.providers import SUPPORTED_PROVIDERS

    if provider not in SUPPORTED_PROVIDERS:
        raise AIError.model_error(f"Unsupported provider: {provider}. Supported providers: {SUPPORTED_PROVIDERS}")

    if not messages:
        raise AIError.model_error("No messages provided for AI generation")

    # Ensure OAuth tokens are fresh for OAuth-based providers
    _ensure_oauth_token(provider)

    # Set up spinner
    if is_group:
        message_type = f"grouped {task_description}s"
    else:
        message_type = task_description

    # Calculate estimated token count for display (input only)
    total_input_tokens = sum(count_tokens(msg.get("content", ""), model) for msg in messages)
    # Also compute exact char count so we can learn the real ratio later.
    input_char_count = sum(len(msg.get("content", "")) for msg in messages)
    formatted_input = f"{total_input_tokens:,}"

    if quiet:
        spinner = None
    else:
        spinner = Status(
            f"Generating {message_type} with ~{formatted_input} input tokens using {provider} {model_name}..."
        )
        spinner.start()

    last_exception: Exception | None = None
    last_error_type = "unknown"

    for attempt in range(max_retries):
        try:
            if not quiet and not skip_success_message and attempt > 0:
                if spinner:
                    spinner.update(f"Retry {attempt + 1}/{max_retries} with {provider} {model_name}...")
                logger.info(f"Retry attempt {attempt + 1}/{max_retries}")

            # Call the appropriate provider function
            provider_func = provider_funcs.get(provider)
            if not provider_func:
                raise AIError.model_error(f"Provider function not found for: {provider}")

            result = provider_func(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                reasoning_effort=reasoning_effort,
            )
            content, prompt_tokens, output_tokens, duration_ms, reasoning_tokens = result

            # Learn the real chars/token ratio for this model when the API
            # reported a positive prompt token count.
            if prompt_tokens > 0 and input_char_count > 0:
                _record_token_ratio(model, input_char_count, prompt_tokens)

            if spinner:
                if skip_success_message:
                    spinner.stop()
                else:
                    spinner.stop()
                    console.print(f"✓ Generated {message_type} with {provider} {model_name}")

            if content is not None and content.strip():
                return (content.strip(), prompt_tokens, output_tokens, duration_ms, reasoning_tokens)
            else:
                logger.warning(f"Empty or None content received from {provider} {model_name}: {repr(content)}")
                raise AIError.model_error("Empty response from AI model")

        except AIError as e:
            last_exception = e
            error_type = e.error_type
            last_error_type = error_type

            # For authentication and model errors, don't retry
            if error_type in ["authentication", "model"]:
                if spinner and not skip_success_message:
                    spinner.stop()
                    console.print(f"✗ Failed to generate {message_type} with {provider} {model_name}")
                raise

            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = 2**attempt
                if not quiet and not skip_success_message:
                    if attempt == 0:
                        logger.warning(f"AI generation failed, retrying in {wait_time}s: {e}")
                    else:
                        logger.warning(f"AI generation failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")

                if spinner and not skip_success_message:
                    for i in range(wait_time, 0, -1):
                        spinner.update(f"Retry {attempt + 1}/{max_retries} in {i}s...")
                        time.sleep(1)
                else:
                    time.sleep(wait_time)
            else:
                retry_word = "retry" if max_retries == 1 else "retries"
                logger.error(f"AI generation failed after {max_retries} {retry_word}: {e}")

    if spinner and not skip_success_message:
        spinner.stop()
        console.print(f"✗ Failed to generate {message_type} with {provider} {model_name}")

    # If we get here, all retries failed - use the last classified error type
    retry_word = "retry" if max_retries == 1 else "retries"
    error_message = f"Failed to generate {message_type} after {max_retries} {retry_word}"
    if last_error_type == "authentication":
        raise AIError.authentication_error(error_message) from last_exception
    elif last_error_type == "rate_limit":
        raise AIError.rate_limit_error(error_message) from last_exception
    elif last_error_type == "timeout":
        raise AIError.timeout_error(error_message) from last_exception
    elif last_error_type == "connection":
        raise AIError.connection_error(error_message) from last_exception
    elif last_error_type == "model":
        raise AIError.model_error(error_message) from last_exception
    else:
        raise AIError.unknown_error(error_message) from last_exception
