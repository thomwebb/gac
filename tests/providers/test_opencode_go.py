"""Tests for OpenCode Go provider."""

import os
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from gac.errors import AIError
from gac.providers import PROVIDER_REGISTRY
from tests.provider_test_utils import assert_missing_api_key_error, temporarily_remove_env_var
from tests.providers.conftest import BaseProviderTest


class TestOpenCodeGoImports:
    """Test that OpenCode Go provider can be imported."""

    def test_import_provider(self):
        """Test that OpenCode Go provider module can be imported."""
        from gac.providers import opencode_go  # noqa: F401

    def test_provider_in_registry(self):
        """Test that provider is registered."""
        assert "opencode-go" in PROVIDER_REGISTRY


class TestOpenCodeGoAPIKeyValidation:
    """Test OpenCode Go API key validation."""

    def test_missing_api_key_error(self):
        """Test that OpenCode Go raises error when API key is missing."""
        with temporarily_remove_env_var("OPENCODE_API_KEY"):
            with pytest.raises(AIError) as exc_info:
                PROVIDER_REGISTRY["opencode-go"]("kimi-k2.6", [], 0.7, 1000)

            assert_missing_api_key_error(exc_info, "opencode-go", "OPENCODE_API_KEY")


class TestOpenCodeGoProviderMocked(BaseProviderTest):
    """Mocked tests for OpenCode Go provider."""

    @property
    def provider_name(self) -> str:
        return "opencode-go"

    @property
    def provider_module(self) -> str:
        return "gac.providers.opencode_go"

    @property
    def api_function(self) -> Callable:
        return PROVIDER_REGISTRY["opencode-go"]

    @property
    def api_key_env_var(self) -> str | None:
        return "OPENCODE_API_KEY"

    @property
    def model_name(self) -> str:
        return "kimi-k2.6"

    @property
    def success_response(self) -> dict[str, Any]:
        return {
            "choices": [{"message": {"content": "feat: Add new feature"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        }

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {
            "choices": [{"message": {"content": ""}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        }


class TestOpenCodeGoEdgeCases:
    """Test edge cases for OpenCode Go provider."""

    def test_opencode_go_missing_choices(self):
        """Test handling of response without choices field."""
        with patch.dict("os.environ", {"OPENCODE_API_KEY": "test-key"}):
            with patch("gac.providers.base.httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"some_field": "value"}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                with pytest.raises(AIError) as exc_info:
                    PROVIDER_REGISTRY["opencode-go"]("kimi-k2.6", [], 0.7, 1000)

                assert exc_info.value.error_type == "model"

    def test_opencode_go_missing_message(self):
        """Test handling of response with choices but no message."""
        with patch.dict("os.environ", {"OPENCODE_API_KEY": "test-key"}):
            with patch("gac.providers.base.httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"choices": [{}]}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                with pytest.raises(AIError) as exc_info:
                    PROVIDER_REGISTRY["opencode-go"]("kimi-k2.6", [], 0.7, 1000)

                assert exc_info.value.error_type == "model"

    def test_opencode_go_null_content(self):
        """Test handling of null content in message."""
        with patch.dict("os.environ", {"OPENCODE_API_KEY": "test-key"}):
            with patch("gac.providers.base.httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"choices": [{"message": {"content": None}}]}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                with pytest.raises(AIError) as exc_info:
                    PROVIDER_REGISTRY["opencode-go"]("kimi-k2.6", [], 0.7, 1000)

                assert "null content" in str(exc_info.value).lower()

    def test_opencode_go_empty_content(self):
        """Test handling of empty content string."""
        with patch.dict("os.environ", {"OPENCODE_API_KEY": "test-key"}):
            with patch("gac.providers.base.httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "choices": [{"message": {"content": ""}}],
                    "usage": {"prompt_tokens": 100, "completion_tokens": 0},
                }
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                with pytest.raises(AIError) as exc_info:
                    PROVIDER_REGISTRY["opencode-go"]("kimi-k2.6", [], 0.7, 1000)

                assert "empty content" in str(exc_info.value).lower()

    def test_opencode_go_model_variants(self):
        """Test that different OpenCode Go models can be specified."""
        with patch.dict("os.environ", {"OPENCODE_API_KEY": "test-key"}):
            with patch("gac.providers.base.httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "choices": [{"message": {"content": "test response"}}],
                    "usage": {"prompt_tokens": 100, "completion_tokens": 50},
                }
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                models = [
                    "kimi-k2.6",
                    "opencode-go/deepseek-v4-pro",
                    "opencode-go/glm-5.1",
                    "opencode-go/qwen3.6-plus",
                ]

                for model in models:
                    result = PROVIDER_REGISTRY["opencode-go"](model, [{"role": "user", "content": "test"}], 0.7, 1000)
                    assert result[0] == "test response"

    def test_opencode_go_token_counting(self):
        """Test token counting from response."""
        with patch.dict("os.environ", {"OPENCODE_API_KEY": "test-key"}):
            with patch("gac.providers.base.httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "choices": [{"message": {"content": "test response"}}],
                    "usage": {"prompt_tokens": 150, "completion_tokens": 75},
                }
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                result = PROVIDER_REGISTRY["opencode-go"]("kimi-k2.6", [{"role": "user", "content": "test"}], 0.7, 1000)

                # Result is (content, prompt_tokens, completion_tokens, reasoning_tokens, total_tokens)
                assert result[0] == "test response"
                assert result[1] == 150  # prompt_tokens
                assert result[2] == 75  # completion_tokens


@pytest.mark.integration
class TestOpenCodeGoIntegration:
    """Integration tests for OpenCode Go provider."""

    def test_real_api_call(self):
        """Test actual OpenCode Go API call with valid credentials."""
        api_key = os.getenv("OPENCODE_API_KEY")
        if not api_key:
            pytest.skip("OPENCODE_API_KEY not set - skipping real API test")

        messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
        response = PROVIDER_REGISTRY["opencode-go"](
            model="kimi-k2.6", messages=messages, temperature=1.0, max_tokens=50
        )

        assert response is not None
        assert isinstance(response, tuple)
        assert len(response[0]) > 0
