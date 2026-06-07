"""Tests for Ollama Cloud provider."""

import os
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from gac.ai_utils import count_tokens
from gac.errors import AIError
from gac.providers import PROVIDER_REGISTRY
from tests.provider_test_utils import assert_import_success
from tests.providers.conftest import BaseProviderTest

call_ollama_cloud_api = PROVIDER_REGISTRY["ollama-cloud"]


class TestOllamaCloudImports:
    """Test that Ollama Cloud provider can be imported."""

    def test_import_provider(self):
        """Test that Ollama Cloud provider module can be imported."""
        from gac.providers import ollama_cloud  # noqa: F401

    def test_provider_in_registry(self):
        """Test that Ollama Cloud provider is in the registry."""
        assert "ollama-cloud" in PROVIDER_REGISTRY
        assert_import_success(PROVIDER_REGISTRY["ollama-cloud"])


class TestOllamaCloudProviderMocked(BaseProviderTest):
    """Mocked tests for Ollama Cloud provider."""

    @property
    def provider_name(self) -> str:
        return "ollama-cloud"

    @property
    def provider_module(self) -> str:
        return "gac.providers.ollama_cloud"

    @property
    def api_function(self) -> Callable:
        return PROVIDER_REGISTRY["ollama-cloud"]

    @property
    def api_key_env_var(self) -> str | None:
        return "OLLAMA_CLOUD_API_KEY"

    @property
    def model_name(self) -> str:
        return "llama3"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"response": "feat: Add new feature"}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"response": ""}


class TestOllamaCloudEdgeCases:
    """Test edge cases for Ollama Cloud provider."""

    def test_ollama_cloud_message_content_format(self):
        """Test response with message.content format."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"message": {"content": "test response"}}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with patch.dict(os.environ, {"OLLAMA_CLOUD_API_KEY": "test-key"}):
                result = call_ollama_cloud_api("llama3", [], 0.7, 1000)
            assert result[0] == "test response"

    def test_ollama_cloud_response_format(self):
        """Test response with response field format."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "test response"}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with patch.dict(os.environ, {"OLLAMA_CLOUD_API_KEY": "test-key"}):
                result = call_ollama_cloud_api("llama3", [], 0.7, 1000)
            assert result[0] == "test response"

    def test_ollama_cloud_fallback_string_format(self):
        """Test fallback to string conversion for unexpected format."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"other_field": "some value"}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with patch.dict(os.environ, {"OLLAMA_CLOUD_API_KEY": "test-key"}):
                result = call_ollama_cloud_api("llama3", [], 0.7, 1000)
            assert "other_field" in result[0]

    def test_ollama_cloud_null_content(self):
        """Test handling of null content in message."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"message": {"content": None}}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with patch.dict(os.environ, {"OLLAMA_CLOUD_API_KEY": "test-key"}):
                with pytest.raises(AIError) as exc_info:
                    call_ollama_cloud_api("llama3", [], 0.7, 1000)

            assert "null content" in str(exc_info.value).lower()

    def test_ollama_cloud_custom_api_url(self):
        """Test custom OLLAMA_CLOUD_BASE_URL environment variable."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "test response"}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with patch.dict(
                os.environ,
                {
                    "OLLAMA_CLOUD_API_KEY": "test-key",
                    "OLLAMA_CLOUD_BASE_URL": "https://custom.ollama.com",
                },
            ):
                result = call_ollama_cloud_api("llama3", [], 0.7, 1000)

            # Verify custom URL was used
            call_args = mock_post.call_args
            assert "https://custom.ollama.com/api/chat" in call_args[0][0]
            assert result[0] == "test response"

    def test_ollama_cloud_missing_api_key(self):
        """Test that missing API key raises authentication error."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "test response"}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            # Remove API key from environment
            env = os.environ.copy()
            env.pop("OLLAMA_CLOUD_API_KEY", None)

            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(AIError) as exc_info:
                    call_ollama_cloud_api("llama3", [], 0.7, 1000)

            assert "api_key" in str(exc_info.value).lower() or "authentication" in str(exc_info.value).lower()

    def test_ollama_cloud_with_api_key(self):
        """Test that API key is included in headers when provided."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "test response"}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with patch.dict(os.environ, {"OLLAMA_CLOUD_API_KEY": "test-key"}):
                result = call_ollama_cloud_api("llama3", [], 0.7, 1000)

            # Verify Authorization header was included
            call_args = mock_post.call_args
            headers = call_args.kwargs["headers"]
            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer test-key"
            assert result[0] == "test response"

    def test_ollama_cloud_connection_error(self):
        """Test handling of connection error when Ollama Cloud is unreachable."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")

            with patch.dict(os.environ, {"OLLAMA_CLOUD_API_KEY": "test-key"}):
                with pytest.raises(AIError) as exc_info:
                    call_ollama_cloud_api("llama3", [], 0.7, 1000)

            error_msg = str(exc_info.value).lower()
            assert "network error" in error_msg or "connection" in error_msg

    def test_ollama_cloud_think_tags_missing_eval_count_no_double_count(self):
        """Think-tag content with missing eval_count should not double-count reasoning tokens.

        When Ollama Cloud returns a thinking model response without eval_count,
        output_tokens should be estimated from content minus reasoning tokens
        (not the raw full content count which includes think tags).
        """
        thinking = "Let me analyze the diff carefully" * 10  # ~340 chars
        full_content = "<thinking>" + thinking + "</thinking>\nfeat: add feature"

        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "message": {"content": full_content},
                # No eval_count or prompt_eval_count -> output_tokens falls back to -1
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with patch.dict(os.environ, {"OLLAMA_CLOUD_API_KEY": "test-key"}):
                result = call_ollama_cloud_api("qwq", [{"role": "user", "content": "hi"}], 0.7, 1000)
            content, prompt_tokens, output_tokens, duration_ms, reasoning_tokens = result

            assert reasoning_tokens > 0, "Reasoning tokens should be estimated from think tags"
            raw_tokens = count_tokens(full_content, "qwq")
            assert output_tokens < raw_tokens, (
                f"output_tokens ({output_tokens}) should be < raw content tokens ({raw_tokens})"
            )
            total = output_tokens + reasoning_tokens
            assert abs(total - raw_tokens) <= raw_tokens * 0.3, (
                f"output+reasoning ({total}) should be within 30% of raw ({raw_tokens})"
            )


@pytest.mark.integration
class TestOllamaCloudIntegration:
    """Integration tests for Ollama Cloud provider."""

    def test_real_api_call(self):
        """Test actual Ollama Cloud API call.

        This test requires:
        1. OLLAMA_CLOUD_API_KEY environment variable set
        2. Valid Ollama Cloud account access

        Without these, the test will be skipped.
        """
        api_key = os.getenv("OLLAMA_CLOUD_API_KEY")
        if not api_key:
            pytest.skip("OLLAMA_CLOUD_API_KEY not set - skipping real API test")

        try:
            messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
            response = call_ollama_cloud_api(model="llama3:7b", messages=messages, temperature=1.0, max_tokens=50)

            assert response is not None
            assert isinstance(response, tuple)
            assert len(response[0]) > 0
        except AIError as e:
            error_str = str(e).lower()
            if "not found" in error_str or "unauthorized" in error_str:
                pytest.skip(f"Ollama Cloud API error - skipping real API test: {e}")
            raise
