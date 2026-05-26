"""Tests for Lilac provider."""

import os
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from gac.errors import AIError
from gac.providers import PROVIDER_REGISTRY
from tests.provider_test_utils import assert_missing_api_key_error, temporarily_remove_env_var
from tests.providers.conftest import BaseProviderTest

call_lilac_api = PROVIDER_REGISTRY["lilac"]


class TestLilacImports:
    """Test that Lilac provider can be imported."""

    def test_import_provider(self):
        """Test that Lilac provider module can be imported."""
        from gac.providers import lilac  # noqa: F401

    def test_provider_in_registry(self):
        """Test that Lilac provider is in the registry."""
        assert "lilac" in PROVIDER_REGISTRY


class TestLilacAPIKeyValidation:
    """Test Lilac API key validation."""

    def test_missing_api_key_error(self):
        """Test that Lilac raises error when API key is missing."""
        with temporarily_remove_env_var("LILAC_API_KEY"):
            with pytest.raises(AIError) as exc_info:
                call_lilac_api("google/gemma-4-31b-it", [], 0.7, 1000)

            assert_missing_api_key_error(exc_info, "lilac", "LILAC_API_KEY")


class TestLilacProviderMocked(BaseProviderTest):
    """Mocked tests for Lilac provider."""

    @property
    def provider_name(self) -> str:
        return "lilac"

    @property
    def provider_module(self) -> str:
        return "gac.providers.lilac"

    @property
    def api_function(self) -> Callable:
        return PROVIDER_REGISTRY["lilac"]

    @property
    def api_key_env_var(self) -> str | None:
        return "LILAC_API_KEY"

    @property
    def model_name(self) -> str:
        return "google/gemma-4-31b-it"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": "feat: Add new feature"}}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": ""}}]}


class TestLilacEdgeCases:
    """Test edge cases for Lilac provider."""

    def test_lilac_null_content(self):
        """Test handling of null content."""
        with patch.dict("os.environ", {"LILAC_API_KEY": "test-key"}):
            with patch("httpx.post") as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"choices": [{"message": {"content": None}}]}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                with pytest.raises(AIError) as exc_info:
                    call_lilac_api("google/gemma-4-31b-it", [], 0.7, 1000)

                assert "null content" in str(exc_info.value).lower()


@pytest.mark.integration
class TestLilacIntegration:
    """Integration tests for Lilac provider."""

    def test_real_api_call(self):
        """Test actual Lilac API call with valid credentials."""
        api_key = os.getenv("LILAC_API_KEY")
        if not api_key:
            pytest.skip("LILAC_API_KEY not set - skipping real API test")

        messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
        try:
            response = call_lilac_api(
                model="google/gemma-4-31b-it",
                messages=messages,
                temperature=1.0,
                max_tokens=1024,
            )

            assert response is not None
            assert isinstance(response, tuple)
            assert len(response[0]) > 0
        except AIError as e:
            error_str = str(e).lower()
            if "401" in error_str or "unauthorized" in error_str or "auth" in error_str:
                pytest.skip(f"Lilac API authentication failed - skipping real API test: {e}")
            elif "429" in error_str or "rate limit" in error_str:
                pytest.skip(f"Lilac API rate limit exceeded - skipping real API test: {e}")
            elif (
                "502" in error_str
                or "503" in error_str
                or "service unavailable" in error_str
                or "connection error" in error_str
            ):
                pytest.skip(f"Lilac API service unavailable - skipping real API test: {e}")
            raise
