"""Tests for the Discord webhook notification helper."""

from __future__ import annotations

from unittest import mock

import httpx
import pytest

from gac import discord_webhook
from gac.discord_webhook import (
    EMBED_COLOR,
    GAC_AVATAR_URL,
    _build_embed,
    _split_subject_body,
    _truncate,
    get_webhook_url,
    notify_commit,
)
from gac.errors import GitError


@pytest.fixture(autouse=True)
def _clear_webhook_env(monkeypatch):
    """Ensure tests start with no webhook URL leaking in from the real env."""
    monkeypatch.delenv("GAC_DISCORD_WEBHOOK_URL", raising=False)


@pytest.fixture
def _stub_git(monkeypatch):
    """Stub git helpers to predictable values."""
    monkeypatch.setattr(discord_webhook, "get_repo_root", lambda: "/tmp/myrepo")
    monkeypatch.setattr(discord_webhook, "get_current_branch", lambda: "main")
    monkeypatch.setattr(discord_webhook, "get_commit_hash", lambda: "abc1234deadbeef")


def test_get_webhook_url_unset_returns_none():
    assert get_webhook_url() is None


def test_get_webhook_url_blank_returns_none(monkeypatch):
    monkeypatch.setenv("GAC_DISCORD_WEBHOOK_URL", "   ")
    assert get_webhook_url() is None


def test_get_webhook_url_returns_stripped_value(monkeypatch):
    monkeypatch.setenv("GAC_DISCORD_WEBHOOK_URL", "  https://example.com/hook  ")
    assert get_webhook_url() == "https://example.com/hook"


def test_notify_commit_noop_when_unset():
    with mock.patch.object(httpx, "post") as mpost:
        assert notify_commit("feat: hi") is False
        mpost.assert_not_called()


def test_notify_commit_posts_embed_payload(monkeypatch, _stub_git):
    monkeypatch.setenv("GAC_DISCORD_WEBHOOK_URL", "https://example.com/hook")

    response = mock.Mock()
    response.raise_for_status.return_value = None
    with mock.patch.object(httpx, "post", return_value=response) as mpost:
        assert notify_commit("feat: cool things\n\nBody line with detail.") is True

    mpost.assert_called_once()
    _, kwargs = mpost.call_args
    payload = kwargs["json"]
    assert payload["username"] == "gac"
    assert payload["avatar_url"] == GAC_AVATAR_URL
    # No plain content — we use embeds for the GitHub-style card.
    assert "content" not in payload
    embed = payload["embeds"][0]
    assert embed["title"] == "feat: cool things"
    assert embed["description"] == "Body line with detail."
    assert embed["color"] == EMBED_COLOR
    assert embed["author"]["name"] == "myrepo · main"
    assert embed["author"]["icon_url"] == GAC_AVATAR_URL
    assert embed["footer"]["text"] == "commit abc1234"


def test_notify_commit_swallows_http_errors(monkeypatch, _stub_git):
    monkeypatch.setenv("GAC_DISCORD_WEBHOOK_URL", "https://example.com/hook")

    with mock.patch.object(httpx, "post", side_effect=httpx.ConnectError("boom")):
        assert notify_commit("anything") is False


def test_build_embed_truncates_long_title_and_description(_stub_git):
    long_subject = "x" * 5000
    long_body = "y" * 10000
    embed = _build_embed(f"{long_subject}\n\n{long_body}")
    assert len(embed["title"]) <= 256
    assert embed["title"].endswith("…")
    assert len(embed["description"]) <= 4096
    assert embed["description"].endswith("…")


def test_build_embed_handles_git_errors(monkeypatch):
    def _raise():
        raise GitError("nope")

    monkeypatch.setattr(discord_webhook, "get_repo_root", _raise)
    monkeypatch.setattr(discord_webhook, "get_current_branch", _raise)
    monkeypatch.setattr(discord_webhook, "get_commit_hash", _raise)

    embed = _build_embed("hello")
    assert "unknown" in embed["author"]["name"]
    assert embed["footer"]["text"] == "commit unknown"
    assert embed["title"] == "hello"


def test_build_embed_subject_only_has_no_description(_stub_git):
    embed = _build_embed("feat: just a subject")
    assert "description" not in embed


def test_build_embed_empty_message_uses_placeholder(_stub_git):
    embed = _build_embed("   \n\n  ")
    assert embed["title"] == "(no subject)"
    assert "description" not in embed


def test_split_subject_body_variants():
    assert _split_subject_body("") == ("", "")
    assert _split_subject_body("just subject") == ("just subject", "")
    assert _split_subject_body("subject\n\nbody here") == ("subject", "body here")
    assert _split_subject_body("subject\nimmediate body") == ("subject", "immediate body")


def test_truncate_noop_when_under_limit():
    assert _truncate("hi", 10) == "hi"


def test_truncate_appends_ellipsis_when_over_limit():
    result = _truncate("abcdefghij", 5)
    assert result == "abcd…"
    assert len(result) == 5
