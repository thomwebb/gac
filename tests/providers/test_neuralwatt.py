"""Tests for Neuralwatt provider."""

import os
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from gac.errors import AIError
from gac.providers import PROVIDER_REGISTRY
from tests.provider_test_utils import (
    assert_missing_api_key_error,
    temporarily_remove_env_var,
    temporarily_set_env_var,
)
from tests.providers.conftest import BaseProviderTest


class TestNeuralwattImports:
    """Test that Neuralwatt provider can be imported."""

    def test_import_provider(self):
        """Test that Neuralwatt provider module can be imported."""
        from gac.providers import neuralwatt  # noqa: F401

    def test_provider_in_registry(self):
        """Test that provider is registered."""
        from gac.providers import PROVIDER_REGISTRY

        assert "neuralwatt" in PROVIDER_REGISTRY


class TestNeuralwattAPIKeyValidation:
    """Test Neuralwatt API key validation."""

    def test_missing_api_key_error(self):
        """Test that Neuralwatt raises error when API key is missing."""
        with temporarily_remove_env_var("NEURALWATT_API_KEY"):
            with pytest.raises(AIError) as exc_info:
                PROVIDER_REGISTRY["neuralwatt"]("qwen3.6-35b-fast", [], 0.7, 1000)

            assert_missing_api_key_error(exc_info, "neuralwatt", "NEURALWATT_API_KEY")


class TestNeuralwattProviderMocked(BaseProviderTest):
    """Mocked tests for Neuralwatt provider."""

    @property
    def provider_name(self) -> str:
        return "neuralwatt"

    @property
    def provider_module(self) -> str:
        return "gac.providers.neuralwatt"

    @property
    def api_function(self) -> Callable:
        return PROVIDER_REGISTRY["neuralwatt"]

    @property
    def api_key_env_var(self) -> str | None:
        return "NEURALWATT_API_KEY"

    @property
    def model_name(self) -> str:
        return "qwen3.6-35b-fast"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": "feat: Add new feature"}}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": ""}}]}


class TestNeuralwattEdgeCases:
    """Test edge cases for Neuralwatt provider."""

    @pytest.fixture(autouse=True)
    def _set_api_key(self):
        """Ensure Neuralwatt API key is present for edge case tests."""
        with temporarily_set_env_var("NEURALWATT_API_KEY", "test-key"):
            yield

    def test_neuralwatt_null_content_in_message(self):
        """Test handling of null content in message.content field."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"choices": [{"message": {"content": None}}]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with pytest.raises(AIError) as exc_info:
                PROVIDER_REGISTRY["neuralwatt"]("qwen3.6-35b-fast", [], 0.7, 1000)

            assert "null content" in str(exc_info.value).lower()

    def test_neuralwatt_empty_content(self):
        """Test handling of empty content in message."""
        with patch("gac.providers.base.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"choices": [{"message": {"content": ""}}]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with pytest.raises(AIError) as exc_info:
                PROVIDER_REGISTRY["neuralwatt"]("qwen3.6-35b-fast", [], 0.7, 1000)

            assert "empty content" in str(exc_info.value).lower()


@pytest.mark.integration
class TestNeuralwattIntegration:
    """Integration tests for Neuralwatt provider."""

    def test_real_api_call(self):
        """Test actual Neuralwatt API call with valid credentials."""
        api_key = os.getenv("NEURALWATT_API_KEY")
        if not api_key:
            pytest.skip("NEURALWATT_API_KEY not set - skipping real API test")

        messages = [{"role": "user", "content": "Say 'test success' and nothing else."}]
        response = PROVIDER_REGISTRY["neuralwatt"](
            model="qwen3.6-35b-fast", messages=messages, temperature=1.0, max_tokens=50
        )

        assert response is not None
        assert isinstance(response, tuple)
        assert len(response[0]) > 0
