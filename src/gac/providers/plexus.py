"""Plexus provider for gac.

Plexus is a universal LLM API gateway and transformation layer that sits
in front of your LLM providers and exposes one consistent API surface.
It provides OpenAI-compatible endpoints with provider routing, failover,
usage tracking, and quorum controls.

Environment variables:
    PLEXUS_API_KEY: Your Plexus API key (e.g., sk-plexus-my-key)
    PLEXUS_BASE_URL: Plexus server URL (default: http://localhost:4000)

See: https://github.com/mcowger/plexus
"""

import os

from gac.providers.base import OpenAICompatibleProvider, ProviderConfig


class PlexusProvider(OpenAICompatibleProvider):
    """Plexus provider for universal LLM API gateway access."""

    config = ProviderConfig(
        name="Plexus",
        api_key_env="PLEXUS_API_KEY",
        base_url="",  # Will be set in __init__
    )

    def __init__(self, config: ProviderConfig):
        """Initialize with base URL from environment."""
        base_url = os.getenv("PLEXUS_BASE_URL", "http://localhost:4000")

        # Ensure the base URL ends with /v1/chat/completions
        if "/v1/chat/completions" not in base_url:
            base_url = base_url.rstrip("/")
            url = f"{base_url}/v1/chat/completions"
        else:
            url = base_url

        config.base_url = url
        super().__init__(config)
