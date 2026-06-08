"""Ollama Cloud API provider for gac.

Ollama Cloud provides cloud-hosted access to Ollama models with an API-compatible
endpoint. Requires an OLLAMA_CLOUD_API_KEY environment variable.

API Reference:
- https://ollama.com/cloud
- Endpoint: https://ollama.com/api/chat
- Models: Same as local Ollama (llama3, mistral, etc.)

Environment Variables:
    OLLAMA_CLOUD_API_KEY: Required API key for Ollama Cloud
"""

import os
from typing import Any

from gac.errors import AIError
from gac.providers.base import (
    OpenAICompatibleProvider,
    ParsedResponse,
    ProviderConfig,
    resolve_reasoning_tokens,
)


class OllamaCloudProvider(OpenAICompatibleProvider):
    """Ollama Cloud provider for cloud-hosted LLM models."""

    config = ProviderConfig(
        name="Ollama Cloud",
        api_key_env="OLLAMA_CLOUD_API_KEY",
        base_url="https://ollama.com/api/chat",
    )

    def __init__(self, config: ProviderConfig):
        """Initialize the Ollama Cloud provider."""
        super().__init__(config)

    def _build_request_body(
        self,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        model: str,
        reasoning_effort: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build Ollama Cloud request body with stream disabled."""
        body: dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
            "stream": False,
            **kwargs,
        }
        if reasoning_effort:
            body["reasoning_effort"] = reasoning_effort
        return body

    def _get_api_key(self) -> str:
        """Get required API key for Ollama Cloud."""
        api_key = os.getenv(self.config.api_key_env)
        if not api_key:
            raise AIError.authentication_error("OLLAMA_CLOUD_API_KEY environment variable is required for Ollama Cloud")
        return api_key

    def _parse_response(self, response: dict[str, Any]) -> ParsedResponse:
        """Parse Ollama Cloud response (message.content format)."""
        from gac.postprocess import extract_think_tag_text

        prompt_tokens = response.get("prompt_eval_count", -1)
        completion_tokens = response.get("eval_count", -1)
        if not isinstance(prompt_tokens, int):
            prompt_tokens = -1
        if not isinstance(completion_tokens, int):
            completion_tokens = -1

        message = response.get("message", {})
        content = message.get("content")

        if content is None:
            raise AIError.model_error("Ollama Cloud API returned null content")
        if content == "":
            raise AIError.model_error("Ollama Cloud API returned empty content")

        # Estimate reasoning tokens from think tags when the API
        # does not report them (common for thinking models).
        think_tag_text = extract_think_tag_text(content)
        reasoning_chars = len(think_tag_text)
        output_chars = len(content) - reasoning_chars
        reasoning_tokens, output_tokens = resolve_reasoning_tokens(
            completion_tokens,
            None,
            reasoning_chars,
            output_chars,
        )

        return ParsedResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
        )
