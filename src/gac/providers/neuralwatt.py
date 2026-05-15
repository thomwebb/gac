"""Neuralwatt API provider for gac."""

from gac.providers.base import OpenAICompatibleProvider, ProviderConfig


class NeuralwattProvider(OpenAICompatibleProvider):
    """Neuralwatt API provider with OpenAI-compatible interface."""

    config = ProviderConfig(
        name="Neuralwatt",
        api_key_env="NEURALWATT_API_KEY",
        base_url="https://api.neuralwatt.com/v1",
    )

    def _get_api_url(self, model: str | None = None) -> str:
        """Get Neuralwatt API URL with /chat/completions endpoint."""
        return f"{self.config.base_url}/chat/completions"
