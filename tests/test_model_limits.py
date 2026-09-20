"""Tests for provider context-window limits and diff budget resolution (issue #79)."""

from gac.constants import (
    DEFAULT_CONTEXT_LIMIT,
    PROVIDER_CONTEXT_LIMITS,
    resolve_context_limit,
    resolve_diff_token_limit,
)
from gac.constants.defaults import Utility


class TestResolveContextLimit:
    """Test provider context window resolution."""

    def test_known_providers(self):
        assert resolve_context_limit("openai:gpt-5.6-luna") == 128_000
        assert resolve_context_limit("anthropic:claude-haiku-4-5") == 200_000
        assert resolve_context_limit("gemini:gemini-3.5-flash-lite") == 1_000_000

    def test_local_runtimes_default_small(self):
        assert resolve_context_limit("ollama:llama3") == 8_192
        assert resolve_context_limit("lm-studio:gemma4") == 8_192

    def test_unknown_provider_falls_back(self):
        assert resolve_context_limit("mystery-provider:some-model") == DEFAULT_CONTEXT_LIMIT

    def test_bare_model_name_falls_back(self):
        assert resolve_context_limit("gemma4") == DEFAULT_CONTEXT_LIMIT

    def test_empty_and_noneish(self):
        assert resolve_context_limit("") == DEFAULT_CONTEXT_LIMIT

    def test_provider_prefix_is_case_insensitive(self):
        assert resolve_context_limit("OpenAI:gpt-5.6-luna") == PROVIDER_CONTEXT_LIMITS["openai"]

    def test_every_registry_provider_has_a_limit(self):
        from gac.providers import SUPPORTED_PROVIDERS

        missing = [p for p in SUPPORTED_PROVIDERS if p not in PROVIDER_CONTEXT_LIMITS]
        assert not missing, f"Providers missing context limits: {missing}"


class TestResolveDiffTokenLimit:
    """Test diff budget derivation from the model context window."""

    def test_small_context_scales_down(self):
        # 8k window * 0.6 = 4915 — far below the 192k default cap
        assert resolve_diff_token_limit("ollama:llama3") == 4915

    def test_large_context_is_capped_by_default(self):
        # 1M window would allow 600k, but the 192k default cap applies
        assert resolve_diff_token_limit("gemini:gemini-3.5-flash-lite") == Utility.DEFAULT_DIFF_TOKEN_LIMIT

    def test_configured_limit_wins_when_smaller(self):
        assert resolve_diff_token_limit("openai:gpt-5.6-luna", configured=50_000) == 50_000

    def test_context_budget_wins_when_smaller(self):
        assert resolve_diff_token_limit("openai:gpt-5.6-luna", configured=500_000) == 76_800

    def test_minimum_budget_floor(self):
        # A hypothetical tiny window cannot push the budget below the floor
        tiny = resolve_diff_token_limit("custom-openai:tiny-model", configured=100)
        assert tiny >= 2048

    def test_explicit_none_uses_default_cap(self):
        assert resolve_diff_token_limit("openai:gpt-5.6-luna") == 76_800


class TestPreprocessUsesResolvedLimit:
    """Test that preprocess entry points derive limits from the model."""

    def test_per_file_diffs_resolves_limit_from_model(self):
        from unittest.mock import patch

        from gac.preprocess import preprocess_per_file_diffs

        per_file = [("src/a.py", "diff --git a/src/a.py b/src/a.py\n@@ -1 +1 @@\n-x\n+y\n")]
        with patch("gac.preprocess.smart_truncate_diff", wraps=None) as mock_trunc:
            mock_trunc.return_value = "processed"
            preprocess_per_file_diffs(per_file, model="ollama:llama3")

        assert mock_trunc.call_args[0][1] == 4915

    def test_per_file_diffs_explicit_limit_overrides(self):
        from unittest.mock import patch

        from gac.preprocess import preprocess_per_file_diffs

        per_file = [("src/a.py", "diff --git a/src/a.py b/src/a.py\n@@ -1 +1 @@\n-x\n+y\n")]
        with patch("gac.preprocess.smart_truncate_diff", wraps=None) as mock_trunc:
            mock_trunc.return_value = "processed"
            preprocess_per_file_diffs(per_file, token_limit=12345, model="gemini:x")

        assert mock_trunc.call_args[0][1] == 12345
