"""OpenCode Go API provider for gac."""

import os

from gac.providers.base import OpenAICompatibleProvider, ProviderConfig


class OpenCodeGoProvider(OpenAICompatibleProvider):
    """OpenCode Go provider using OpenAI-compatible API format.

    OpenCode Go provides access to 14+ state-of-the-art open-source models
    including Kimi K2.6, DeepSeek V4 Pro, GLM-5.1, Qwen3.6 Plus, and more.
    """

    config = ProviderConfig(
        name="OpenCode Go",
        api_key_env="OPENCODE_API_KEY",
        base_url="",  # Set in __init__
    )

    def __init__(self, config: ProviderConfig):
        base_url = os.getenv("OPENCODE_BASE_URL", "https://api.opencode.ai")
        config.base_url = f"{base_url.rstrip('/')}/v1"
        super().__init__(config)

    def _get_api_url(self, model: str | None = None) -> str:
        """Get OpenCode Go API URL with /chat/completions endpoint."""
        return f"{self.config.base_url}/chat/completions"
