"""Atlas Cloud chat completions provider."""

import os
from dataclasses import replace

from gac.providers.base import OpenAICompatibleProvider, ProviderConfig


class AtlasCloudProvider(OpenAICompatibleProvider):
    """Use Atlas Cloud credentials and preserve catalog model IDs."""

    config = ProviderConfig(
        name="Atlas Cloud",
        api_key_env="ATLASCLOUD_API_KEY",
        base_url="https://api.atlascloud.ai/v1",
    )

    def __init__(self, config: ProviderConfig):
        base_url = os.getenv("ATLASCLOUD_BASE_URL", config.base_url).rstrip("/")
        super().__init__(replace(config, base_url=base_url))

    def _get_api_url(self, model: str | None = None) -> str:
        return f"{self.config.base_url}/chat/completions"
