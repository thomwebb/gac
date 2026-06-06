"""Tests for Plexus provider."""

import os
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from gac.errors import AIError
from gac.providers import PROVIDER_REGISTRY
from tests.provider_test_utils import assert_missing_api_key_error, temporarily_remove_env_var
from tests.providers.conftest import BaseProviderTest

call_plexus_api = PROVIDER_REGISTRY["plexus"]


class TestPlexusImports:
    """Test that Plexus provider can be imported."""

    def test_import_provider(self):
        """Test that Plexus provider module can be imported."""

    def test_provider_in_registry(self):
        """Test that Plexus provider is in the registry."""
        assert "plexus" in PROVIDER_REGISTRY


class TestPlexusAPIKeyValidation:
    """Test Plexus API key validation."""

    def test_missing_api_key_error(self):
        """Test that Plexus raises error when API key is missing."""
        with temporarily_remove_env_var("PLEXUS_API_KEY"):
            with pytest.raises(AIError) as exc_info:
                call_plexus_api("gpt-4", [], 0.7, 1000)

            assert_missing_api_key_error(exc_info, "plexus", "PLEXUS_API_KEY")

    def test_default_base_url_error(self):
        """Test that Plexus uses default base URL when not set."""
        with temporarily_remove_env_var("PLEXUS_BASE_URL"):
            with patch.dict(os.environ, {"PLEXUS_API_KEY": "test-key"}):
                with patch("gac.providers.base.httpx.post") as mock_post:
                    mock_response = MagicMock()
                    mock_response.json.return_value = {"choices": [{"message": {"content": "test"}}]}
                    mock_response.raise_for_status = MagicMock()
                    mock_post.return_value = mock_response

                    call_plexus_api("gpt-4", [], 0.7, 100)

                    # Should use default URL http://localhost:4000
                    called_url = mock_post.call_args[0][0]
                    assert called_url == "http://localhost:4000/v1/chat/completions"


class TestPlexusProviderMocked(BaseProviderTest):
    """Mocked tests for Plexus provider."""

    @property
    def provider_name(self) -> str:
        return "plexus"

    @property
    def provider_module(self) -> str:
        return "gac.providers.plexus"

    @property
    def api_function(self) -> Callable:
        return PROVIDER_REGISTRY["plexus"]

    @property
    def api_key_env_var(self) -> str | None:
        return "PLEXUS_API_KEY"

    @property
    def model_name(self) -> str:
        return "fast-model"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": "feat: Add new feature"}}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": ""}}]}

    def test_successful_api_call(self):
        """Test that the provider successfully processes a valid API response."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_post.return_value = self._create_mock_response(self.success_response)

            messages = [{"role": "user", "content": "Generate a commit message"}]

            with patch.dict(
                os.environ,
                {"PLEXUS_API_KEY": "sk-plexus-test", "PLEXUS_BASE_URL": "https://plexus.example.com"},
            ):
                result = self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

            assert isinstance(result, tuple)
            assert len(result) == 5
            content, prompt_tokens, output_tokens, duration_ms, reasoning_tokens = result
            assert content == "feat: Add new feature"
            assert isinstance(duration_ms, int) and duration_ms >= 0
            assert isinstance(reasoning_tokens, int) and reasoning_tokens >= 0
            mock_post.assert_called_once()

    def test_empty_content_handling(self):
        """Test that the provider raises an error for empty content."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_post.return_value = self._create_mock_response(self.empty_content_response)

            messages = [{"role": "user", "content": "Generate a commit message"}]

            with patch.dict(
                os.environ,
                {"PLEXUS_API_KEY": "sk-plexus-test", "PLEXUS_BASE_URL": "https://plexus.example.com"},
            ):
                with pytest.raises(Exception) as exc_info:
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

                error_msg = str(exc_info.value).lower()
                assert "empty content" in error_msg or "missing" in error_msg

    def test_http_401_authentication_error(self):
        """Test that the provider handles HTTP 401 authentication errors."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_post.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", request=MagicMock(), response=mock_response
            )

            messages = [{"role": "user", "content": "Generate a commit message"}]

            with patch.dict(
                os.environ,
                {"PLEXUS_API_KEY": "sk-plexus-test", "PLEXUS_BASE_URL": "https://plexus.example.com"},
            ):
                with pytest.raises(AIError):
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

    def test_http_429_rate_limit_error(self):
        """Test that the provider handles HTTP 429 rate limit errors."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"
            mock_post.side_effect = httpx.HTTPStatusError(
                "429 Rate limit exceeded", request=MagicMock(), response=mock_response
            )

            messages = [{"role": "user", "content": "Generate a commit message"}]

            with patch.dict(
                os.environ,
                {"PLEXUS_API_KEY": "sk-plexus-test", "PLEXUS_BASE_URL": "https://plexus.example.com"},
            ):
                with pytest.raises(AIError):
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

    def test_http_500_server_error(self):
        """Test that the provider handles HTTP 500 server errors."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_post.side_effect = httpx.HTTPStatusError(
                "500 Internal server error", request=MagicMock(), response=mock_response
            )

            messages = [{"role": "user", "content": "Generate a commit message"}]

            with patch.dict(
                os.environ,
                {"PLEXUS_API_KEY": "sk-plexus-test", "PLEXUS_BASE_URL": "https://plexus.example.com"},
            ):
                with pytest.raises(AIError):
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

    def test_http_503_service_unavailable(self):
        """Test that the provider handles HTTP 503 service unavailable errors."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 503
            mock_response.text = "Service unavailable"
            mock_post.side_effect = httpx.HTTPStatusError(
                "503 Service unavailable", request=MagicMock(), response=mock_response
            )

            messages = [{"role": "user", "content": "Generate a commit message"}]

            with patch.dict(
                os.environ,
                {"PLEXUS_API_KEY": "sk-plexus-test", "PLEXUS_BASE_URL": "https://plexus.example.com"},
            ):
                with pytest.raises(AIError):
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

    def test_connection_error(self):
        """Test that the provider handles connection errors."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")

            messages = [{"role": "user", "content": "Generate a commit message"}]

            with patch.dict(
                os.environ,
                {"PLEXUS_API_KEY": "sk-plexus-test", "PLEXUS_BASE_URL": "https://plexus.example.com"},
            ):
                with pytest.raises(AIError):
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

    def test_timeout_error(self):
        """Test that the provider handles timeout errors."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timed out")

            messages = [{"role": "user", "content": "Generate a commit message"}]

            with patch.dict(
                os.environ,
                {"PLEXUS_API_KEY": "sk-plexus-test", "PLEXUS_BASE_URL": "https://plexus.example.com"},
            ):
                with pytest.raises(AIError):
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)

    def test_malformed_json_response(self):
        """Test that the provider handles malformed JSON responses."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            messages = [{"role": "user", "content": "Generate a commit message"}]

            with patch.dict(
                os.environ,
                {"PLEXUS_API_KEY": "sk-plexus-test", "PLEXUS_BASE_URL": "https://plexus.example.com"},
            ):
                with pytest.raises((AIError, ValueError, KeyError, TypeError)):
                    self.api_function(model=self.model_name, messages=messages, temperature=0.7, max_tokens=100)


class TestPlexusEdgeCases:
    """Test edge cases for Plexus provider."""

    def test_plexus_null_content(self):
        """Test handling of null content."""
        with patch.dict(
            "os.environ", {"PLEXUS_API_KEY": "sk-plexus-test", "PLEXUS_BASE_URL": "https://plexus.example.com"}
        ):
            with patch("httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"choices": [{"message": {"content": None}}]}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                with pytest.raises(AIError) as exc_info:
                    call_plexus_api("fast-model", [], 0.7, 1000)

                assert "null content" in str(exc_info.value).lower()

    def test_base_url_trailing_slash_handling(self):
        """Test that trailing slashes in base URL are handled correctly."""
        with patch.dict(
            "os.environ",
            {"PLEXUS_API_KEY": "sk-plexus-test", "PLEXUS_BASE_URL": "https://plexus.example.com/"},
        ):
            with patch("httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"choices": [{"message": {"content": "test"}}]}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                call_plexus_api("fast-model", [], 0.7, 1000)

                called_url = mock_post.call_args[0][0]
                assert called_url == "https://plexus.example.com/v1/chat/completions"

    def test_base_url_with_full_path_included(self):
        """Test that full endpoint path in base URL is preserved."""
        with patch.dict(
            "os.environ",
            {
                "PLEXUS_API_KEY": "sk-plexus-test",
                "PLEXUS_BASE_URL": "https://plexus.example.com/v1/chat/completions",
            },
        ):
            with patch("httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"choices": [{"message": {"content": "test"}}]}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                call_plexus_api("fast-model", [], 0.7, 1000)

                called_url = mock_post.call_args[0][0]
                assert called_url == "https://plexus.example.com/v1/chat/completions"

    def test_authorization_header(self):
        """Test that the API key is correctly added to the Authorization header."""
        with patch("httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"choices": [{"message": {"content": "test"}}]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with patch.dict(
                "os.environ",
                {"PLEXUS_API_KEY": "sk-plexus-test", "PLEXUS_BASE_URL": "https://plexus.example.com"},
            ):
                call_plexus_api("fast-model", [], 0.7, 1000)

                # Check that Authorization header is set correctly
                call_kwargs = mock_post.call_args[1]
                headers = call_kwargs["headers"]
                assert headers["Authorization"] == "Bearer sk-plexus-test"


@pytest.mark.integration
class TestPlexusIntegration:
    """Integration tests for Plexus provider."""

    def test_real_api_call(self):
        """Test actual Plexus API call with valid credentials."""
        api_key = os.getenv("PLEXUS_API_KEY")
        base_url = os.getenv("PLEXUS_BASE_URL")

        if not api_key or not base_url:
            pytest.skip("PLEXUS_API_KEY and PLEXUS_BASE_URL not set - skipping real API test")

        messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
        response = call_plexus_api(model="fast-model", messages=messages, temperature=1.0, max_tokens=1024)

        assert response is not None
        assert isinstance(response, tuple)
        assert len(response[0]) > 0
