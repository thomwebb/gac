"""DeepInfra API provider for gac."""

import os

from gac.providers.base import OpenAICompatibleProvider, ProviderConfig


class DeepInfraProvider(OpenAICompatibleProvider):
    """DeepInfra OpenAI-compatible provider with custom base URL."""

    config = ProviderConfig(
        name="DeepInfra",
        api_key_env="DEEPINFRA_API_KEY",
        base_url="",  # Will be set in __init__
    )

    def __init__(self, config: ProviderConfig):
        base_url = os.getenv("DEEPINFRA_BASE_URL", "https://api.deepinfra.com")
        config.base_url = f"{base_url.rstrip('/')}/v1/openai"
        super().__init__(config)

    def _get_api_url(self, model: str | None = None) -> str:
        return f"{self.config.base_url}/chat/completions"
