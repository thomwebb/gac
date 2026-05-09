"""Claude Code API provider for gac.

This provider allows users with Claude Code subscriptions to use their OAuth tokens
instead of paying for the expensive Anthropic API.
"""

from typing import Any

from gac.errors import AIError
from gac.oauth.claude_code import load_stored_token
from gac.providers.base import AnthropicCompatibleProvider, ProviderConfig


class ClaudeCodeProvider(AnthropicCompatibleProvider):
    """Claude Code OAuth provider with special system message requirements."""

    config = ProviderConfig(
        name="Claude Code",
        api_key_env="CLAUDE_CODE_ACCESS_TOKEN",
        base_url="https://api.anthropic.com/v1",
    )

    def _get_api_key(self) -> str:
        """Get OAuth token from token store."""
        token = load_stored_token()
        if token:
            return token

        raise AIError.authentication_error(
            "Claude Code authentication not found. Run 'gac auth claude-code login' to authenticate."
        )

    def _build_headers(self) -> dict[str, str]:
        """Build headers with OAuth token and special anthropic-beta."""
        headers = super()._build_headers()
        # Replace x-api-key with Bearer token
        if "x-api-key" in headers:
            del headers["x-api-key"]
        headers["Authorization"] = f"Bearer {self.api_key}"
        # Add special OAuth beta header
        headers["anthropic-beta"] = "oauth-2025-04-20"
        return headers

    def _build_request_body(
        self,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        model: str,
        reasoning_effort: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build Anthropic-style request with fixed system message.

        IMPORTANT: Claude Code OAuth tokens require the system message to be EXACTLY
        "You are Claude Code, Anthropic's official CLI for Claude." with NO additional content.
        Any other instructions must be moved to the first user message.

        Delegates to the parent class for standard Anthropic formatting, then overrides
        just the system message. reasoning_effort is accepted for signature consistency
        but not applied.
        """
        # Let parent handle message conversion (reasoning_effort passed through but
        # not applied by AnthropicCompatibleProvider)
        body = super()._build_request_body(
            messages, temperature, max_tokens, model, reasoning_effort=reasoning_effort, **kwargs
        )

        # Remove user-supplied system instructions (parent put them in body["system"])
        # and move them to the first user message content.
        user_system = body.pop("system", "")
        if user_system and body["messages"]:
            body["messages"][0]["content"] = f"{user_system}\n\n{body['messages'][0]['content']}"

        # Set the exact system message required by Claude Code OAuth
        body["system"] = "You are Claude Code, Anthropic's official CLI for Claude."

        return body
