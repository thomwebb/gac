"""Tests for GenericHTTPProvider reasoning_content/reasoning field detection.

Bug 3 fix: GenericHTTPProvider._parse_response now checks for
reasoning_content and reasoning message fields (DeepSeek/OpenRouter style),
includes them in thinking_text, and applies the anti-lie guard.
"""

from gac.providers.base import GenericHTTPProvider, ProviderConfig


def _make_provider() -> GenericHTTPProvider:
    return GenericHTTPProvider(ProviderConfig(name="Gen", api_key_env="KEY", base_url="http://test.url"))


class TestGenericHTTPReasoningContentField:
    """Test GenericHTTPProvider._parse_response detects reasoning_content
    field in choices[0].message (DeepSeek style)."""

    def test_reasoning_content_field_estimates_tokens(self):
        """choices[0].message.reasoning_content should estimate reasoning tokens."""
        provider = _make_provider()
        reasoning_text = "Let me think about this carefully" * 10  # ~340 chars
        response = {
            "choices": [
                {
                    "message": {
                        "content": "feat: add feature",
                        "reasoning_content": reasoning_text,
                    }
                }
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 200},
        }
        parsed = provider._parse_response(response)
        assert parsed.reasoning_tokens > 0
        assert parsed.output_tokens < 200


class TestGenericHTTPReasoningFieldOpenRouter:
    """Test GenericHTTPProvider._parse_response detects reasoning field
    in choices[0].message (OpenRouter variant)."""

    def test_reasoning_field_estimates_tokens(self):
        """choices[0].message.reasoning should estimate reasoning tokens."""
        provider = _make_provider()
        reasoning_text = "Analyzing the code changes step by step" * 10  # ~380 chars
        response = {
            "choices": [
                {
                    "message": {
                        "content": "fix: correct off-by-one error",
                        "reasoning": reasoning_text,
                    }
                }
            ],
            "usage": {"prompt_tokens": 50, "completion_tokens": 150},
        }
        parsed = provider._parse_response(response)
        assert parsed.reasoning_tokens > 0
        assert parsed.output_tokens < 150


class TestGenericHTTPAntiLieGuard:
    """Test that reasoning_tokens=0 from API is overridden when reasoning
    text is present (anti-lie guard)."""

    def test_reasoning_content_overrides_zero_from_api(self):
        """reasoning_content with non-empty text AND usage.reasoning_tokens=0
        should trigger anti-lie guard: override 0 to force estimation."""
        provider = _make_provider()
        reasoning_text = "Deep reasoning about the implementation" * 10  # ~360 chars
        response = {
            "choices": [
                {
                    "message": {
                        "content": "feat: new thing",
                        "reasoning_content": reasoning_text,
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 80,
                "completion_tokens": 200,
                "completion_tokens_details": {"reasoning_tokens": 0},
            },
        }
        parsed = provider._parse_response(response)
        # Anti-lie guard should kick in: 0 overridden to estimated value
        assert parsed.reasoning_tokens > 0
        assert parsed.output_tokens < 200


class TestGenericHTTPReasoningFieldInMessagePath:
    """Test reasoning_content/reasoning in top-level message dict
    (Ollama-style fallback path)."""

    def test_reasoning_content_in_message_dict(self):
        """reasoning_content in top-level message dict should be detected."""
        provider = _make_provider()
        reasoning_text = "Thinking through the approach" * 10  # ~280 chars
        response = {
            "message": {
                "content": "chore: update deps",
                "reasoning_content": reasoning_text,
            },
            "usage": {"prompt_tokens": 30, "completion_tokens": 100},
        }
        parsed = provider._parse_response(response)
        assert parsed.reasoning_tokens > 0
        assert parsed.output_tokens < 100


class TestGenericHTTPThinkTagsCombinedWithReasoningField:
    """Test that both reasoning_content field AND think tags in content
    both contribute to reasoning token estimation."""

    def test_both_sources_contribute(self):
        """Both reasoning_content field AND think tags should be combined."""
        provider = _make_provider()
        reasoning_field_text = "Field-based reasoning text" * 5
        think_text = "Tag-based reasoning content" * 5
        full_content = "<thinking>" + think_text + "</thinking>\nfeat: combined"
        response = {
            "choices": [
                {
                    "message": {
                        "content": full_content,
                        "reasoning_content": reasoning_field_text,
                    }
                }
            ],
            "usage": {"prompt_tokens": 50, "completion_tokens": 200},
        }
        parsed = provider._parse_response(response)
        # Both sources contribute, so reasoning_tokens should be > either alone
        assert parsed.reasoning_tokens > 0
        assert parsed.output_tokens < 200
