"""Discord webhook notifications for successful gac commits.

Posts a polished embed-style notification to a user-configured Discord webhook
every time a commit lands. Configuration lives in ``$HOME/.gac.env`` under the
``GAC_DISCORD_WEBHOOK_URL`` key and is set up via ``gac init``.

If the URL is unset, every function here is a no-op. Network failures are
swallowed (logged at warning level) so we never block a successful commit on a
flaky webhook.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any

import httpx

from gac.errors import GitError
from gac.git import get_commit_hash, get_current_branch, get_repo_root

logger = logging.getLogger(__name__)

# Provided by the user — the cute lil' emoji avatar for the webhook.
GAC_AVATAR_URL = "https://cdn.discordapp.com/emojis/1444427616160321679.webp"
GAC_USERNAME = "gac"
WEBHOOK_TIMEOUT_SECONDS = 5.0
ENV_KEY = "GAC_DISCORD_WEBHOOK_URL"

# A pleasant green for "commit succeeded" (matches GitHub's merge-green vibe).
EMBED_COLOR = 0x2DA44E

# Discord embed field limits (per official docs).
_MAX_TITLE_LEN = 256
_MAX_DESCRIPTION_LEN = 4096


def _repo_name() -> str:
    """Best-effort repo name from the repo root; falls back to ``unknown``."""
    try:
        return os.path.basename(get_repo_root()) or "unknown"
    except GitError:
        return "unknown"


def _safe_git(call: Callable[[], str], default: str = "unknown") -> str:
    """Call a git helper; on GitError return the default. Don't block commits."""
    try:
        return call()
    except GitError:
        return default


def _truncate(text: str, limit: int) -> str:
    """Truncate text to ``limit`` chars, appending an ellipsis if cut."""
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _split_subject_body(commit_message: str) -> tuple[str, str]:
    """Split a commit message into (subject, body) using the conventional blank-line rule."""
    stripped = commit_message.strip()
    if not stripped:
        return "", ""
    parts = stripped.split("\n", 1)
    subject = parts[0].strip()
    body = parts[1].strip() if len(parts) > 1 else ""
    return subject, body


def _build_embed(commit_message: str) -> dict[str, Any]:
    """Build a Discord embed payload that mimics GitHub-style commit cards."""
    repo = _repo_name()
    branch = _safe_git(get_current_branch)
    full_hash = _safe_git(get_commit_hash, default="")
    short_hash = full_hash[:7] if full_hash else "unknown"

    subject, body = _split_subject_body(commit_message)
    title = _truncate(subject or "(no subject)", _MAX_TITLE_LEN)
    description = _truncate(body, _MAX_DESCRIPTION_LEN) if body else ""

    embed: dict[str, Any] = {
        "title": title,
        "color": EMBED_COLOR,
        "author": {"name": f"{repo} · {branch}", "icon_url": GAC_AVATAR_URL},
        "footer": {"text": f"commit {short_hash}"},
    }
    if description:
        embed["description"] = description
    return embed


def get_webhook_url() -> str | None:
    """Return the configured webhook URL, or None if not set / blank."""
    raw = os.getenv(ENV_KEY)
    if raw is None:
        return None
    value = raw.strip()
    return value or None


def notify_commit(commit_message: str) -> bool:
    """Send a commit notification to the configured Discord webhook.

    Returns ``True`` if a message was sent successfully, ``False`` otherwise
    (including when no webhook is configured). Never raises.
    """
    url = get_webhook_url()
    if not url:
        return False

    payload = {
        "username": GAC_USERNAME,
        "avatar_url": GAC_AVATAR_URL,
        "embeds": [_build_embed(commit_message)],
    }

    try:
        response = httpx.post(url, json=payload, timeout=WEBHOOK_TIMEOUT_SECONDS)
        response.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning("Discord webhook notification failed: %s", e)
        return False
    return True
