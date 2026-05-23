"""CLI for managing the Discord webhook integration.

Subcommands:
- ``gac discord setup``  — interactively configure (or replace) the webhook URL.
- ``gac discord remove`` — delete the webhook URL from $HOME/.gac.env.
- ``gac discord show``   — display whether a webhook is configured (URL masked).
- ``gac discord test``   — send a test notification to the configured webhook.
"""

from __future__ import annotations

import os
from pathlib import Path

import click
import questionary
from dotenv import load_dotenv, set_key, unset_key

from gac.discord_webhook import ENV_KEY, notify_commit

GAC_ENV_PATH = Path.home() / ".gac.env"


def _mask_url(url: str) -> str:
    """Return a masked preview of a URL so it's safe to display."""
    if len(url) <= 30:
        return url
    return f"{url[:30]}…"


def _load_existing_url() -> str | None:
    """Read the current webhook URL from $HOME/.gac.env, if any."""
    if not GAC_ENV_PATH.exists():
        return None
    load_dotenv(GAC_ENV_PATH, override=True)
    value = os.getenv(ENV_KEY)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _prompt_for_url() -> str | None:
    """Prompt the user for a webhook URL. Returns None on cancel / invalid."""
    response = questionary.text("Discord webhook URL:").ask()
    if response is None:
        click.echo("Cancelled.")
        return None
    url: str = str(response).strip()
    if not url:
        click.echo("No URL provided. Cancelled.")
        return None
    if not url.startswith(("http://", "https://")):
        click.echo("That doesn't look like a URL (must start with http:// or https://).")
        return None
    return url


def _save_url(url: str) -> None:
    """Persist the webhook URL to $HOME/.gac.env."""
    GAC_ENV_PATH.touch(exist_ok=True)
    set_key(str(GAC_ENV_PATH), ENV_KEY, url)
    os.environ[ENV_KEY] = url  # keep current process in sync, e.g. for `discord test`
    click.echo("Discord webhook saved.")


@click.group()
def discord() -> None:
    """Manage the Discord webhook integration for commit notifications."""
    pass


@discord.command()
def setup() -> None:
    """Interactively configure a Discord webhook URL."""
    click.echo("Discord Webhook Setup")
    click.echo(
        "gac can ping a Discord channel every time you make a commit, using a\n"
        "webhook URL from your channel's integration settings.\n"
    )

    existing = _load_existing_url()
    if existing:
        choice = questionary.select(
            f"A Discord webhook is already configured ({_mask_url(existing)}). What now?",
            choices=[
                "Keep current webhook",
                "Replace with a new webhook URL",
                "Remove the webhook",
            ],
            use_shortcuts=True,
            use_arrow_keys=True,
            use_jk_keys=False,
        ).ask()

        if choice is None or choice.startswith("Keep"):
            click.echo("Keeping existing Discord webhook.")
            return
        if choice.startswith("Remove"):
            unset_key(str(GAC_ENV_PATH), ENV_KEY)
            os.environ.pop(ENV_KEY, None)
            click.echo("Removed Discord webhook.")
            return
        # Otherwise fall through to prompt for a new URL.

    url = _prompt_for_url()
    if url is None:
        return
    _save_url(url)


@discord.command()
def remove() -> None:
    """Remove the configured Discord webhook URL."""
    existing = _load_existing_url()
    if existing is None:
        click.echo("No Discord webhook is currently configured.")
        return
    unset_key(str(GAC_ENV_PATH), ENV_KEY)
    os.environ.pop(ENV_KEY, None)
    click.echo("Removed Discord webhook.")


@discord.command()
def show() -> None:
    """Display whether a Discord webhook is configured (URL masked)."""
    existing = _load_existing_url()
    if existing is None:
        click.echo("No Discord webhook configured.")
        click.echo("Run 'uvx gac discord setup' to configure one.")
        return
    click.echo(f"Discord webhook configured: {_mask_url(existing)}")


@discord.command()
def test() -> None:
    """Send a test notification to the configured Discord webhook."""
    existing = _load_existing_url()
    if existing is None:
        click.echo("No Discord webhook configured.")
        click.echo("Run 'uvx gac discord setup' to configure one first.")
        return

    test_message = (
        "test: 🐶 Biscuit barking from gac discord test\n\n"
        "If you can see this in your Discord channel, the webhook is wired up correctly!"
    )
    if notify_commit(test_message):
        click.echo("✓ Test notification sent successfully.")
    else:
        click.echo("✗ Failed to send test notification. Check the URL and your network.")
