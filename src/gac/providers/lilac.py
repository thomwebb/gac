"""Lilac API provider for gac."""

import os

from gac.providers.base import OpenAICompatibleProvider, ProviderConfig


class LilacProvider(OpenAICompatibleProvider):
    """Lilac OpenAI-compatible provider with custom base URL."""

    config = ProviderConfig(
        name="Lilac",
        api_key_env="LILAC_API_KEY",
        base_url="",  # Will be set in __init__
    )

    def __init__(self, config: ProviderConfig):
        """Initialize with base URL from environment or default."""
        base_url = os.getenv("LILAC_BASE_URL", "https://api.getlilac.com")
        config.base_url = f"{base_url.rstrip('/')}/v1"
        super().__init__(config)

    def _get_api_url(self, model: str | None = None) -> str:
        """Get Lilac API URL with /chat/completions endpoint."""
        return f"{self.config.base_url}/chat/completions"
