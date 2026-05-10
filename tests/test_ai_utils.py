"""Unit tests for AI utility functions.

These tests run without any external dependencies and test core logic.
"""

import os
import sys
from unittest.mock import MagicMock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

import gac.ai_utils as ai_utils  # noqa: E402
from gac.errors import AIError  # noqa: E402


class TestCountTokens:
    """Test count_tokens function."""

    @staticmethod
    def _reset_learned_store(monkeypatch, tmp_path):
        """Helper: isolate the learned-ratios store to a temp file."""
        temp_store = tmp_path / "test_ratios.json"
        monkeypatch.setattr(ai_utils, "_TOKEN_RATIOS_PATH", temp_store, raising=True)
        monkeypatch.setattr(ai_utils, "_ratios_loaded", False, raising=True)
        ai_utils._LEARNED_RATIOS.clear()
        monkeypatch.setattr(ai_utils, "_save_learned_ratios", lambda ratios: None, raising=True)

    def test_count_tokens(self, monkeypatch, tmp_path):
        """Test character-based token counting with clean learned state."""
        self._reset_learned_store(monkeypatch, tmp_path)

        # Test with string content - "Hello, world!" = 13 chars
        # 13 / 3.4 = 3.82, rounded = 4 tokens
        text = "Hello, world!"
        token_count = ai_utils.count_tokens(text, "openai:gpt-4")
        assert token_count == 4  # Should return calculated token count
        assert isinstance(token_count, int)

        # Test different text length
        text = "This is a test message"  # 22 chars
        # 22 / 3.4 = 6.47, rounded = 6 tokens
        token_count = ai_utils.count_tokens(text, "openai:gpt-4")
        assert token_count == 6

        # Test with list format
        messages = [{"role": "user", "content": "Hello"}]  # 5 chars
        # 5 / 3.4 = 1.47, rounded = 1 token
        token_count = ai_utils.count_tokens(messages, "openai:gpt-4")
        assert token_count == 1

        # Test with empty string vs no characters
        assert ai_utils.count_tokens("", "openai:gpt-4") == 0
        assert ai_utils.count_tokens("   ", "openai:gpt-4") == 1  # 3 spaces = 3/3.4 = 0.88, rounded = 1

    def test_count_tokens_empty_content(self, monkeypatch, tmp_path):
        """Test token counting with empty content."""
        self._reset_learned_store(monkeypatch, tmp_path)
        assert ai_utils.count_tokens("", "openai:gpt-4") == 0
        assert ai_utils.count_tokens([], "openai:gpt-4") == 0
        assert ai_utils.count_tokens({}, "openai:gpt-4") == 0

    def test_all_providers_use_same_character_based_counting(self, monkeypatch, tmp_path):
        """Test that all unlearned providers use the same default ratio."""
        self._reset_learned_store(monkeypatch, tmp_path)

        text = "Hello, world!"  # 13 chars
        # 13 / 3.4 = 3.82, rounded = 4 tokens
        expected_tokens = round(len(text) / 3.4)

        # Test various providers - all should give the same result (unlearned)
        providers_and_models = [
            "openai:gpt-4",
            "anthropic:claude-3",
            "ollama:llama2",
            "lm-studio:local-model",
            "custom-openai:local-gpt4",
            "custom-anthropic:local-claude",
            "groq:llama3-70b",
            "gemini:gemini-pro",
        ]

        for model in providers_and_models:
            token_count = ai_utils.count_tokens(text, model)
            assert token_count == expected_tokens, (
                f"Provider {model} should give {expected_tokens} tokens, got {token_count}"
            )

    def test_character_based_calculation_examples(self, monkeypatch, tmp_path):
        """Test specific examples of character-based token calculation."""
        self._reset_learned_store(monkeypatch, tmp_path)

        test_cases = [
            ("Hello", 1),  # 5 chars / 3.4 = 1.47 -> 1 token
            ("Hello world", 3),  # 11 chars / 3.4 = 3.24 -> 3 tokens
            ("This is a test", 4),  # 14 chars / 3.4 = 4.12 -> 4 tokens
            ("", 0),  # Empty string = 0 tokens
            ("a", 1),  # 1 char / 3.4 = 0.29 -> rounded = 0, but we force 1 for non-empty
        ]

        for text, expected_tokens in test_cases:
            token_count = ai_utils.count_tokens(text, "openai:gpt-4")
            assert token_count == expected_tokens, (
                f"Text '{text}' should give {expected_tokens} tokens, got {token_count}"
            )

    def test_character_based_calculation_edge_cases(self, monkeypatch, tmp_path):
        """Test edge cases for character-based token calculation."""
        self._reset_learned_store(monkeypatch, tmp_path)

        # Test very short text
        assert ai_utils.count_tokens("a", "openai:gpt-4") == 1  # 1 char, forced to 1 token

        # Test long text
        long_text = "a" * 100  # 100 chars
        # 100 / 3.4 = 29.41 -> 29 tokens
        expected = round(100 / 3.4)
        assert ai_utils.count_tokens(long_text, "openai:gpt-4") == expected

        # Test with spaces and newlines
        text_with_spaces = "Hello \n\n world"  # 14 chars including spaces and newlines
        expected = round(14 / 3.4)  # = 4 tokens
        actual = ai_utils.count_tokens(text_with_spaces, "openai:gpt-4")
        assert actual == expected, f"Expected {expected}, got {actual}"

    def test_character_based_calculation_accuracy(self, monkeypatch, tmp_path):
        """Test that character-based calculation gives reasonable results."""
        self._reset_learned_store(monkeypatch, tmp_path)

        # Test that our calculation gives consistent results
        text = "The quick brown fox jumps over the lazy dog"
        token_count = ai_utils.count_tokens(text, "any:model")

        # Should be the same as the direct calculation
        expected = round(len(text) / 3.4)
        assert token_count == expected

        # Should be reasonable for this text (not way off)
        assert 10 <= token_count <= 15  # Reasonable range for this sentence

        # Test that different content lengths scale appropriately
        short_text = "Hi"
        medium_text = "This is a medium length message"
        long_text = short_text * 50

        short_tokens = ai_utils.count_tokens(short_text, "any:model")
        medium_tokens = ai_utils.count_tokens(medium_text, "any:model")
        long_tokens = ai_utils.count_tokens(long_text, "any:model")

        assert short_tokens < medium_tokens < long_tokens


class TestAIError:
    """Test AIError class."""

    def test_ai_error_class_exists(self):
        """Test that AIError class exists and can be instantiated."""
        error = AIError("Test error")
        assert str(error) == "Test error"

    def test_ai_error_with_type(self):
        """Test AIError with error type."""
        error = AIError("Test error", error_type="model")
        assert error.error_type == "model"


class TestGenerateWithRetries:
    def test_unsupported_provider(self):
        with pytest.raises(AIError) as e:
            ai_utils.generate_with_retries({}, "bad:model", [], 0.7, 100, 1, True)
        assert e.value.error_type == "model"

    def test_empty_messages(self):
        with pytest.raises(AIError) as e:
            ai_utils.generate_with_retries({}, "openai:gpt-4", [], 0.7, 100, 1, True)
        assert e.value.error_type == "model"

    def test_missing_provider_func(self):
        with pytest.raises(AIError) as e:
            ai_utils.generate_with_retries({}, "openai:gpt-4", [{"role": "user", "content": "x"}], 0.7, 100, 1, True)
        assert e.value.error_type == "model"

    @patch("gac.ai_utils.Status")
    def test_skip_success_message(self, mock_status):
        mock_spinner = MagicMock()
        mock_status.return_value = mock_spinner
        funcs = {"openai": lambda **kw: ("ok", 1, 1, 100, 0)}
        ai_utils.generate_with_retries(
            funcs, "openai:gpt-4", [{"role": "user", "content": "x"}], 0.7, 100, 1, False, False, True
        )
        mock_spinner.stop.assert_called_once()

    def test_empty_content(self):
        funcs = {"openai": lambda **kw: ("", 0, 0, 0, 0)}
        with pytest.raises(AIError) as e:
            ai_utils.generate_with_retries(funcs, "openai:gpt-4", [{"role": "user", "content": "x"}], 0.7, 100, 1, True)
        assert e.value.error_type == "model"

    def test_none_content(self):
        funcs = {"openai": lambda **kw: (None, 0, 0, 0, 0)}
        with pytest.raises(AIError) as e:
            ai_utils.generate_with_retries(funcs, "openai:gpt-4", [{"role": "user", "content": "x"}], 0.7, 100, 1, True)
        assert e.value.error_type == "model"

    @patch("gac.ai_utils.Status")
    @patch("gac.ai_utils.console")
    def test_auth_error_spinner_fail(self, mock_console, mock_status):
        mock_spinner = MagicMock()
        mock_status.return_value = mock_spinner

        def raise_auth_error(**kw):
            raise AIError.authentication_error("Invalid API key")

        funcs = {"openai": raise_auth_error}
        with pytest.raises(AIError):
            ai_utils.generate_with_retries(
                funcs, "openai:gpt-4", [{"role": "user", "content": "x"}], 0.7, 100, 1, False
            )
        mock_spinner.stop.assert_called()
        mock_console.print.assert_called_once()

    @patch("gac.ai_utils.time.sleep")
    def test_retry_warning(self, mock_sleep):
        call_count = [0]

        def func(**kw):
            call_count[0] += 1
            if call_count[0] < 2:
                raise AIError.connection_error("fail")
            return ("ok", 1, 1, 100, 0)

        funcs = {"openai": func}
        ai_utils.generate_with_retries(funcs, "openai:gpt-4", [{"role": "user", "content": "x"}], 0.7, 100, 2, True)
        assert call_count[0] == 2

    def test_final_auth_error(self):
        def raise_auth_error(**kw):
            raise AIError.authentication_error("Invalid API key")

        funcs = {"openai": raise_auth_error}
        with pytest.raises(AIError) as e:
            ai_utils.generate_with_retries(funcs, "openai:gpt-4", [{"role": "user", "content": "x"}], 0.7, 100, 2, True)
        assert e.value.error_type == "authentication"

    def test_final_model_error(self):
        def raise_model_error(**kw):
            raise AIError.model_error("Model not found")

        funcs = {"openai": raise_model_error}
        with pytest.raises(AIError) as e:
            ai_utils.generate_with_retries(funcs, "openai:gpt-4", [{"role": "user", "content": "x"}], 0.7, 100, 2, True)
        assert e.value.error_type == "model"

    def test_final_unknown_error(self):
        """Test unknown error handling path (line 241)."""

        def raise_unknown_error(**kw):
            # Create an AIError with no specific type
            error = AIError("Something went wrong")
            error.error_type = "something_else"  # Unknown type
            raise error

        funcs = {"openai": raise_unknown_error}
        with pytest.raises(AIError) as e:
            ai_utils.generate_with_retries(funcs, "openai:gpt-4", [{"role": "user", "content": "x"}], 0.7, 100, 2, True)
        assert e.value.error_type == "unknown"
        assert "Failed to generate" in str(e.value) and "after 2 retries" in str(e.value)


class TestEstimateReasoningTokens:
    """Test estimate_reasoning_tokens function."""

    def test_empty_string(self):
        """Empty string returns 0."""
        assert ai_utils.estimate_reasoning_tokens("") == 0

    def test_short_text(self):
        """Short reasoning text produces at least 1 token."""
        # "think" = 5 chars → 5/3.4 = 1.47 → round = 1
        assert ai_utils.estimate_reasoning_tokens("think") == 1

    def test_medium_text(self):
        """Medium reasoning text estimation."""
        # 34 chars → 34/3.4 = 10 tokens
        text = "a" * 34
        assert ai_utils.estimate_reasoning_tokens(text) == 10

    def test_long_text(self):
        """Long reasoning text (like real model output) estimation."""
        # Simulating ~1000 chars of thinking → ~294 tokens
        text = "thinking about this problem " * 37  # ~999 chars
        result = ai_utils.estimate_reasoning_tokens(text)
        assert result > 0
        # Should be roughly len/3.4, within a reasonable range
        expected = round(len(text) / 3.4)
        assert result == expected

    def test_consistent_with_count_tokens_ratio(self):
        """Same char count should give same token count as count_tokens."""
        text = "some reasoning content here"
        from gac.ai_utils import count_tokens

        # Both use the same 3.4 ratio
        assert ai_utils.estimate_reasoning_tokens(text) == count_tokens(text, "any-model")

    def test_whitespace_only(self):
        """Whitespace-only text should estimate as 0 tokens."""
        # Whitespace-only reasoning is not meaningful; return 0
        text = " " * 34
        assert ai_utils.estimate_reasoning_tokens(text) == 0

    def test_newline_heavy_text(self):
        """Newline-heavy reasoning text with actual content counts code points."""
        # Mix of newlines and content: not whitespace-only
        text = "reasoning" + "\n" * 34
        assert ai_utils.estimate_reasoning_tokens(text) > 0

    def test_cjk_text(self):
        """CJK characters are counted by code point (not bytes)."""
        # CJK chars are 3 bytes in UTF-8 but 1 code point each.
        # len() counts code points, so 34 CJK chars → 10 tokens.
        text = "思" * 34
        assert ai_utils.estimate_reasoning_tokens(text) == 10

    def test_emoji_text(self):
        """Emoji are counted by code point."""
        # Some emoji are multi-code-point but len() counts code points.
        # Simple emoji: 1 code point each. 34 → 10 tokens.
        text = "🤔" * 34
        assert ai_utils.estimate_reasoning_tokens(text) == 10


class TestNormalizeReasoningTokens:
    """Test normalize_reasoning_tokens function."""

    def test_explicit_tokens_win(self):
        """Explicit token count > 0 is returned as-is."""
        assert ai_utils.normalize_reasoning_tokens(15, "some thinking text") == 15

    def test_explicit_zero_means_zero(self):
        """Explicit 0 means the API reported zero reasoning tokens — no estimation."""
        assert ai_utils.normalize_reasoning_tokens(0, "A" * 340) == 0

    def test_none_sentinel_falls_back_to_estimate(self):
        """When explicit_tokens is None (not reported), estimate from text."""
        text = "A" * 34  # 10 tokens
        assert ai_utils.normalize_reasoning_tokens(None, text) == 10

    def test_none_sentinel_empty_text_returns_zero(self):
        """When not reported and text is empty, return 0."""
        assert ai_utils.normalize_reasoning_tokens(None, "") == 0

    def test_large_explicit_ignores_empty_text(self):
        """Large explicit token count works fine with empty text."""
        assert ai_utils.normalize_reasoning_tokens(5000, "") == 5000

    def test_explicit_zero_ignores_text(self):
        """Explicit 0 ignores even long reasoning text."""
        assert ai_utils.normalize_reasoning_tokens(0, "thinking" * 100) == 0

    def test_estimate_whitespace_only_returns_zero(self):
        """Whitespace-only reasoning text should estimate as 0 tokens."""
        from gac.ai_utils import estimate_reasoning_tokens

        assert estimate_reasoning_tokens("   \n\n   \t  ") == 0
        assert estimate_reasoning_tokens("  ") == 0


class TestAllocateReasoningTokens:
    """Test allocate_reasoning_tokens — proportional token allocation."""

    def test_proportional_split_with_api_tokens(self):
        """When API reports completion_tokens, split proportionally by chars."""
        from gac.ai_utils import allocate_reasoning_tokens

        # 1000 total tokens, 2000 reasoning chars, 500 output chars.
        # share = 2000/2500 = 0.8, reasoning = round(1000 * 0.8) = 800
        result = allocate_reasoning_tokens(1000, 2000, 500)
        assert result == 800

    def test_proportional_split_sums_to_total(self):
        """reasoning + output should always equal completion_tokens."""
        from gac.ai_utils import allocate_reasoning_tokens

        completion = 500
        reasoning = allocate_reasoning_tokens(completion, 3000, 1200)
        # 500 * (3000/4200) = 357.14 → 357
        assert reasoning == 357
        assert reasoning + (completion - reasoning) == completion

    def test_no_reasoning_returns_zero(self):
        """Zero reasoning chars → 0 reasoning tokens."""
        from gac.ai_utils import allocate_reasoning_tokens

        assert allocate_reasoning_tokens(100, 0, 200) == 0

    def test_all_reasoning_gets_all_tokens(self):
        """When all text is reasoning, all tokens go to reasoning."""
        from gac.ai_utils import allocate_reasoning_tokens

        assert allocate_reasoning_tokens(100, 2000, 0) == 100

    def test_unknown_completion_falls_back_to_estimation(self):
        """When completion_tokens is -1, fall back to char-based estimation."""
        from gac.ai_utils import allocate_reasoning_tokens

        # With -1: estimate_reasoning_tokens("A" * 340) = 100
        result = allocate_reasoning_tokens(-1, 340, 100)
        assert result == 100  # 340 / 3.4 = 100

    def test_zero_total_chars_returns_zero(self):
        """Both reasoning and output at zero → 0 reasoning tokens."""
        from gac.ai_utils import allocate_reasoning_tokens

        assert allocate_reasoning_tokens(100, 0, 0) == 0

    def test_minimum_one_token_when_reasoning_exists(self):
        """Very small reasoning share still returns at least 1 token."""
        from gac.ai_utils import allocate_reasoning_tokens

        # 10 tokens, 1 reasoning char, 9999 output chars → tiny share, but >= 1
        result = allocate_reasoning_tokens(10, 1, 9999)
        assert result >= 1


class TestEnsureOAuthToken:
    """Tests for ensure_oauth_token covering chatgpt-oauth and copilot branches."""

    def test_chatgpt_oauth_token_valid(self) -> None:
        from gac.ai_utils import _ensure_oauth_token

        with (
            patch("gac.oauth.chatgpt.is_token_expired", return_value=False),
            patch("gac.ai_utils.TokenStore") as mock_store,
        ):
            mock_instance = MagicMock()
            mock_instance.get_token.return_value = {"access_token": "tok"}
            mock_store.return_value = mock_instance
            # Should not raise
            _ensure_oauth_token("chatgpt-oauth")
            assert os.environ.get("CHATGPT_OAUTH_API_KEY") == "tok"
        os.environ.pop("CHATGPT_OAUTH_API_KEY", None)

    def test_chatgpt_oauth_token_expired_refresh_success(self) -> None:
        from gac.ai_utils import _ensure_oauth_token

        with (
            patch("gac.oauth.chatgpt.is_token_expired", return_value=True),
            patch("gac.oauth.chatgpt.refresh_access_token", return_value={"access_token": "new_tok"}),
            patch("gac.ai_utils.TokenStore") as mock_store,
        ):
            mock_instance = MagicMock()
            mock_instance.get_token.return_value = {"access_token": "new_tok"}
            mock_store.return_value = mock_instance
            _ensure_oauth_token("chatgpt-oauth")
            assert os.environ.get("CHATGPT_OAUTH_API_KEY") == "new_tok"
        os.environ.pop("CHATGPT_OAUTH_API_KEY", None)

    def test_chatgpt_oauth_token_expired_refresh_fails(self) -> None:
        from gac.ai_utils import _ensure_oauth_token
        from gac.errors import AIError

        with (
            patch("gac.oauth.chatgpt.is_token_expired", return_value=True),
            patch("gac.oauth.chatgpt.refresh_access_token", return_value=None),
        ):
            with pytest.raises(AIError, match="token not found or expired"):
                _ensure_oauth_token("chatgpt-oauth")

    def test_copilot_token_valid(self) -> None:
        from gac.ai_utils import _ensure_oauth_token

        with (
            patch("gac.oauth.copilot.refresh_token_if_expired", return_value=True),
            patch("gac.ai_utils.TokenStore") as mock_store,
        ):
            mock_instance = MagicMock()
            mock_instance.get_token.return_value = {"access_token": "cop_tok"}
            mock_store.return_value = mock_instance
            _ensure_oauth_token("copilot")
            assert os.environ.get("COPILOT_OAUTH_TOKEN") == "cop_tok"
        os.environ.pop("COPILOT_OAUTH_TOKEN", None)

    def test_copilot_token_invalid(self) -> None:
        from gac.ai_utils import _ensure_oauth_token
        from gac.errors import AIError

        with patch("gac.oauth.copilot.refresh_token_if_expired", return_value=False):
            with pytest.raises(AIError, match="token not found or expired"):
                _ensure_oauth_token("copilot")

    def test_token_store_missing_access_token(self) -> None:
        from gac.ai_utils import _ensure_oauth_token
        from gac.errors import AIError

        with (
            patch("gac.oauth.chatgpt.is_token_expired", return_value=False),
            patch("gac.ai_utils.TokenStore") as mock_store,
        ):
            mock_instance = MagicMock()
            mock_instance.get_token.return_value = {"refresh_token": "but_no_access"}
            mock_store.return_value = mock_instance
            with pytest.raises(AIError, match="token not found"):
                _ensure_oauth_token("chatgpt-oauth")

    def test_token_store_returns_none(self) -> None:
        from gac.ai_utils import _ensure_oauth_token
        from gac.errors import AIError

        with (
            patch("gac.oauth.chatgpt.is_token_expired", return_value=False),
            patch("gac.ai_utils.TokenStore") as mock_store,
        ):
            mock_instance = MagicMock()
            mock_instance.get_token.return_value = None
            mock_store.return_value = mock_instance
            with pytest.raises(AIError, match="token not found"):
                _ensure_oauth_token("chatgpt-oauth")


class TestTokenRatioClamping:
    """Test that learned token ratios are clamped to sane bounds."""

    @staticmethod
    def _reset_learned_store(monkeypatch, tmp_path):
        """Helper: isolate the learned-ratios store to a temp file."""
        temp_store = tmp_path / "test_ratios.json"
        monkeypatch.setattr(ai_utils, "_TOKEN_RATIOS_PATH", temp_store, raising=True)
        monkeypatch.setattr(ai_utils, "_ratios_loaded", False, raising=True)
        ai_utils._LEARNED_RATIOS.clear()
        # Allow real _save_learned_ratios to write to the temp store.
        monkeypatch.setattr(ai_utils, "_TOKEN_RATIOS_PATH", temp_store, raising=True)

    def test_load_clamps_poison_value(self, monkeypatch, tmp_path):
        """A poison ratio (95.0) in the JSON file is clamped to _MAX_RATIO on load."""
        import json

        self._reset_learned_store(monkeypatch, tmp_path)
        temp_store = ai_utils._TOKEN_RATIOS_PATH

        # Write a JSON file with an absurd ratio for "test-model"
        temp_store.write_text(json.dumps({"test-model": 95.0}))

        # Force reload
        monkeypatch.setattr(ai_utils, "_ratios_loaded", False, raising=True)
        loaded = ai_utils._load_learned_ratios()

        assert "test-model" in loaded
        # Should be clamped to _MAX_RATIO (6.0), not the poison 95.0
        assert loaded["test-model"] == ai_utils._MAX_RATIO
        assert loaded["test-model"] < 10.0  # Sanity

    def test_load_clamps_below_minimum(self, monkeypatch, tmp_path):
        """A ratio below _MIN_RATIO (e.g. 0.5) is clamped up."""
        import json

        self._reset_learned_store(monkeypatch, tmp_path)
        temp_store = ai_utils._TOKEN_RATIOS_PATH

        temp_store.write_text(json.dumps({"test-model": 0.5}))

        monkeypatch.setattr(ai_utils, "_ratios_loaded", False, raising=True)
        loaded = ai_utils._load_learned_ratios()

        assert "test-model" in loaded
        assert loaded["test-model"] == ai_utils._MIN_RATIO

    def test_count_tokens_clamps_in_memory_value(self, monkeypatch, tmp_path):
        """Even if a poison value somehow gets into _LEARNED_RATIOS, count_tokens clamps it."""
        self._reset_learned_store(monkeypatch, tmp_path)

        # Bypass normal loading and inject a poison ratio directly.
        ai_utils._LEARNED_RATIOS["poison-model"] = 95.0
        ai_utils._ratios_loaded = True

        # 340 chars / 95.0 = 3.57 → rounds to 4 (uncapped: absurdly low)
        # But with clamping: 340 / 6.0 = 56.67 → rounds to 57
        text = "a" * 340
        result = ai_utils.count_tokens(text, "openai:poison-model")

        # The clamp forces ratio ≤ 6.0, so tokens ≥ ceil(340/6) = 57.
        assert result >= 57
        # Also ensure it's not the poison-collapsed value.
        assert result > 10  # Poison would give ~4

    def test_record_token_ratio_clamps_outlier(self, monkeypatch, tmp_path):
        """_record_token_ratio clamps extreme observations to [_MIN_RATIO, _MAX_RATIO]."""
        self._reset_learned_store(monkeypatch, tmp_path)

        # Simulate an absurd observation: 100 chars, 1 token → ratio 100.0
        ai_utils._record_token_ratio("openai:clamp-test", char_count=100, token_count=1)

        # After recording, the stored ratio must be clamped.
        loaded = ai_utils._load_learned_ratios()
        assert "clamp-test" in loaded
        assert loaded["clamp-test"] <= ai_utils._MAX_RATIO

    def test_default_ratio_is_within_bounds(self):
        """_DEFAULT_RATIO itself is within [_MIN_RATIO, _MAX_RATIO]."""
        assert ai_utils._MIN_RATIO <= ai_utils._DEFAULT_RATIO <= ai_utils._MAX_RATIO
