"""Tests for the optional Atlas Cloud provider."""

import os
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from gac.errors import AIError
from gac.providers import PROVIDER_REGISTRY
from gac.providers.atlascloud import AtlasCloudProvider
from tests.providers.conftest import BaseProviderTest

call_atlascloud_api = PROVIDER_REGISTRY["atlascloud"]


class TestAtlasCloudImports:
    def test_import_provider(self):
        from gac.providers import atlascloud

        assert atlascloud.AtlasCloudProvider is AtlasCloudProvider

    def test_provider_in_registry(self):
        assert "atlascloud" in PROVIDER_REGISTRY


class TestAtlasCloudAPIKeyValidation:
    def test_openai_key_is_not_used(self, monkeypatch):
        monkeypatch.delenv("ATLASCLOUD_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        with pytest.raises(AIError, match="ATLASCLOUD_API_KEY"), patch("httpx.post") as post:
            call_atlascloud_api("openai/gpt-4.1-mini", [], 0.7, 32)
        post.assert_not_called()


class TestAtlasCloudProviderMocked(BaseProviderTest):
    @property
    def provider_name(self) -> str:
        return "atlascloud"

    @property
    def provider_module(self) -> str:
        return "gac.providers.atlascloud"

    @property
    def api_function(self) -> Callable:
        return call_atlascloud_api

    @property
    def api_key_env_var(self) -> str | None:
        return "ATLASCLOUD_API_KEY"

    @property
    def model_name(self) -> str:
        return "openai/gpt-4.1-mini"

    @property
    def success_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": "feat: Add new feature"}}]}

    @property
    def empty_content_response(self) -> dict[str, Any]:
        return {"choices": [{"message": {"content": ""}}]}


class TestAtlasCloudEdgeCases:
    def test_request_and_usage(self, monkeypatch):
        monkeypatch.setenv("ATLASCLOUD_API_KEY", "test-atlas-key")
        monkeypatch.delenv("ATLASCLOUD_BASE_URL", raising=False)
        messages = [{"role": "user", "content": "Write a commit message."}]
        response = MagicMock()
        response.json.return_value = {
            "choices": [{"message": {"content": "feat: add provider"}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 4},
        }
        with patch("httpx.post", return_value=response) as post:
            result = call_atlascloud_api("openai/gpt-4.1-mini", messages, 0.2, 64)
        post.assert_called_once()
        assert post.call_args.args[0] == "https://api.atlascloud.ai/v1/chat/completions"
        assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-atlas-key"
        body = post.call_args.kwargs["json"]
        assert body["model"] == "openai/gpt-4.1-mini"
        assert body["messages"] == messages
        assert body["temperature"] == 0.2
        assert body["max_tokens"] == 64
        assert result[:3] == ("feat: add provider", 12, 4)

    def test_base_override_does_not_mutate_shared_config(self, monkeypatch):
        monkeypatch.setenv("ATLASCLOUD_BASE_URL", "https://gateway.example/v1/")
        custom = AtlasCloudProvider(AtlasCloudProvider.config)
        assert custom._get_api_url() == "https://gateway.example/v1/chat/completions"
        monkeypatch.delenv("ATLASCLOUD_BASE_URL")
        default = AtlasCloudProvider(AtlasCloudProvider.config)
        assert default._get_api_url() == "https://api.atlascloud.ai/v1/chat/completions"

    def test_null_content(self, monkeypatch):
        monkeypatch.setenv("ATLASCLOUD_API_KEY", "test-atlas-key")
        response = MagicMock()
        response.json.return_value = {"choices": [{"message": {"content": None}}]}
        with patch("httpx.post", return_value=response), pytest.raises(AIError, match="null content"):
            call_atlascloud_api("openai/gpt-4.1-mini", [], 0.7, 32)


@pytest.mark.integration
class TestAtlasCloudIntegration:
    def test_real_api_call(self):
        if not os.getenv("ATLASCLOUD_API_KEY"):
            pytest.skip("ATLASCLOUD_API_KEY not set")
        response = call_atlascloud_api(
            "openai/gpt-4.1-mini", [{"role": "user", "content": "Say test success."}], 0.2, 32
        )
        assert response[0].strip()
