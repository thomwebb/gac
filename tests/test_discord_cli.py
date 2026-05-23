"""Tests for the ``gac discord`` subcommand group."""

from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

from gac import discord_cli
from gac.discord_cli import discord


@contextmanager
def _patch_env_path(env_path: Path):
    with (
        mock.patch.object(discord_cli, "GAC_ENV_PATH", env_path),
        mock.patch.dict("os.environ", {}, clear=False),
    ):
        # Ensure no stale value from the real env leaks in.
        from gac.discord_webhook import ENV_KEY

        if ENV_KEY in __import__("os").environ:
            del __import__("os").environ[ENV_KEY]
        yield


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def env_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / ".gac.env"


# ---------- setup ----------


def test_setup_first_time_saves_url(runner, env_file):
    with _patch_env_path(env_file), mock.patch("questionary.text") as mtext:
        mtext.return_value.ask.return_value = "https://discord.com/api/webhooks/abc/def"
        result = runner.invoke(discord, ["setup"])
        assert result.exit_code == 0
        assert "Discord webhook saved." in result.output
        assert "GAC_DISCORD_WEBHOOK_URL" in env_file.read_text()


def test_setup_rejects_non_url(runner, env_file):
    with _patch_env_path(env_file), mock.patch("questionary.text") as mtext:
        mtext.return_value.ask.return_value = "not-a-url"
        result = runner.invoke(discord, ["setup"])
        assert result.exit_code == 0
        assert "doesn't look like a URL" in result.output
        assert not env_file.exists() or "GAC_DISCORD_WEBHOOK_URL" not in env_file.read_text()


def test_setup_cancelled_at_url_prompt(runner, env_file):
    with _patch_env_path(env_file), mock.patch("questionary.text") as mtext:
        mtext.return_value.ask.return_value = None
        result = runner.invoke(discord, ["setup"])
        assert result.exit_code == 0
        assert "Cancelled." in result.output


def test_setup_existing_keep(runner, env_file):
    env_file.write_text("GAC_DISCORD_WEBHOOK_URL='https://example.com/hook'\n")
    with _patch_env_path(env_file), mock.patch("questionary.select") as msel:
        msel.return_value.ask.return_value = "Keep current webhook"
        result = runner.invoke(discord, ["setup"])
        assert result.exit_code == 0
        assert "Keeping existing" in result.output
        assert "https://example.com/hook" in env_file.read_text()


def test_setup_existing_remove(runner, env_file):
    env_file.write_text("GAC_DISCORD_WEBHOOK_URL='https://example.com/hook'\n")
    with _patch_env_path(env_file), mock.patch("questionary.select") as msel:
        msel.return_value.ask.return_value = "Remove the webhook"
        result = runner.invoke(discord, ["setup"])
        assert result.exit_code == 0
        assert "Removed Discord webhook." in result.output
        assert "GAC_DISCORD_WEBHOOK_URL" not in env_file.read_text()


def test_setup_existing_replace(runner, env_file):
    env_file.write_text("GAC_DISCORD_WEBHOOK_URL='https://example.com/old'\n")
    with (
        _patch_env_path(env_file),
        mock.patch("questionary.select") as msel,
        mock.patch("questionary.text") as mtext,
    ):
        msel.return_value.ask.return_value = "Replace with a new webhook URL"
        mtext.return_value.ask.return_value = "https://example.com/new"
        result = runner.invoke(discord, ["setup"])
        assert result.exit_code == 0
        assert "Discord webhook saved." in result.output
        contents = env_file.read_text()
        assert "https://example.com/new" in contents
        assert "https://example.com/old" not in contents


# ---------- remove ----------


def test_remove_when_unset(runner, env_file):
    with _patch_env_path(env_file):
        result = runner.invoke(discord, ["remove"])
        assert result.exit_code == 0
        assert "No Discord webhook is currently configured." in result.output


def test_remove_when_set(runner, env_file):
    env_file.write_text("GAC_DISCORD_WEBHOOK_URL='https://example.com/hook'\n")
    with _patch_env_path(env_file):
        result = runner.invoke(discord, ["remove"])
        assert result.exit_code == 0
        assert "Removed Discord webhook." in result.output
        assert "GAC_DISCORD_WEBHOOK_URL" not in env_file.read_text()


# ---------- show ----------


def test_show_when_unset(runner, env_file):
    with _patch_env_path(env_file):
        result = runner.invoke(discord, ["show"])
        assert result.exit_code == 0
        assert "No Discord webhook configured." in result.output


def test_show_masks_long_url(runner, env_file):
    long_url = "https://discord.com/api/webhooks/" + "X" * 100
    env_file.write_text(f"GAC_DISCORD_WEBHOOK_URL='{long_url}'\n")
    with _patch_env_path(env_file):
        result = runner.invoke(discord, ["show"])
        assert result.exit_code == 0
        assert "…" in result.output
        # The full secret tail should not leak.
        assert long_url not in result.output


# ---------- test ----------


def test_test_when_unset(runner, env_file):
    with _patch_env_path(env_file):
        result = runner.invoke(discord, ["test"])
        assert result.exit_code == 0
        assert "No Discord webhook configured." in result.output


def test_test_invokes_notify_commit(runner, env_file):
    env_file.write_text("GAC_DISCORD_WEBHOOK_URL='https://example.com/hook'\n")
    with (
        _patch_env_path(env_file),
        mock.patch.object(discord_cli, "notify_commit", return_value=True) as mnotify,
    ):
        result = runner.invoke(discord, ["test"])
        assert result.exit_code == 0
        assert "Test notification sent successfully." in result.output
        mnotify.assert_called_once()


def test_test_reports_failure(runner, env_file):
    env_file.write_text("GAC_DISCORD_WEBHOOK_URL='https://example.com/hook'\n")
    with (
        _patch_env_path(env_file),
        mock.patch.object(discord_cli, "notify_commit", return_value=False),
    ):
        result = runner.invoke(discord, ["test"])
        assert result.exit_code == 0
        assert "Failed to send test notification" in result.output
