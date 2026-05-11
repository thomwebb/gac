"""CLI for configuring reasoning effort interactively.

Provides both a standalone `gac reasoning` subcommand and a reusable
workflow function consumed by `gac init` and `gac model`.
"""

from pathlib import Path

import click
import questionary
from dotenv import dotenv_values, set_key, unset_key

GAC_ENV_PATH = Path.home() / ".gac.env"

_VALID_REASONING_EFFORT_VALUES = {"low", "medium", "high"}


def configure_reasoning_effort_workflow(env_path: Path | str) -> bool:
    """Configure reasoning effort, used by both init and model workflows.

    Reads the current value from the env file (if any), shows the
    existing setting with keep/change/disable options, or presents the
    full choice list for first-time configuration.

    Args:
        env_path: Path to the environment file

    Returns:
        True if configuration completed successfully, False if cancelled
    """
    env_path = Path(env_path) if isinstance(env_path, str) else env_path

    existing = dotenv_values(str(env_path))
    existing_re = existing.get("GAC_REASONING_EFFORT")
    existing_re_norm = existing_re.strip().lower() if isinstance(existing_re, str) else None
    existing_valid = bool(existing_re_norm and existing_re_norm in _VALID_REASONING_EFFORT_VALUES)

    click.echo()

    if existing_re:
        if existing_valid:
            click.echo(f"Reasoning Effort — currently: {existing_re_norm}")
        else:
            click.echo(f"Reasoning Effort — currently: {existing_re} [invalid]")
            click.echo("This must be one of: low, medium, high — or unset to use the model default.")

        re_action = questionary.select(
            "How would you like to proceed?",
            choices=[
                *([f"Keep existing ({existing_re_norm})"] if existing_valid else []),
                "Select new value",
                "Disable (use model default)",
            ],
            use_shortcuts=True,
            use_arrow_keys=True,
            use_jk_keys=False,
        ).ask()
        if re_action is None:
            click.echo("Reasoning effort configuration cancelled. Leaving unchanged.")
            return True  # Not a hard failure — user skipped, existing value stays
        if re_action.startswith("Keep existing"):
            click.echo(f"Keeping GAC_REASONING_EFFORT={existing_re_norm}")
            return True
        if re_action.startswith("Disable"):
            unset_key(str(env_path), "GAC_REASONING_EFFORT")
            click.echo("GAC_REASONING_EFFORT unset. Model default will be used.")
            return True
        # "Select new value" — fall through to the full choice list
    else:
        click.echo(
            "Reasoning Effort\n"
            "Controls how much internal reasoning a model performs before responding.\n"
            "If your model doesn't support `reasoning_effort` or you're not sure, choose Skip."
        )

    # Full choice list (first time or "Select new value" from existing)
    re_choice = questionary.select(
        "Select reasoning effort:",
        choices=["Skip (use model default)", "low", "medium", "high"],
        use_shortcuts=True,
        use_arrow_keys=True,
        use_jk_keys=False,
    ).ask()
    if re_choice is None:
        click.echo("Reasoning effort selection cancelled. Leaving unchanged.")
        return True  # Not a failure — user skipped
    if re_choice.startswith("Skip"):
        unset_key(str(env_path), "GAC_REASONING_EFFORT")
        click.echo("GAC_REASONING_EFFORT unset. Model default will be used.")
    else:
        set_key(str(env_path), "GAC_REASONING_EFFORT", re_choice)
        click.echo(f"Set GAC_REASONING_EFFORT={re_choice}")

    return True


@click.command()
def reasoning() -> None:
    """Configure reasoning effort for AI commit message generation."""
    click.echo("Configure reasoning effort for commit message generation:\n")

    if not GAC_ENV_PATH.exists():
        GAC_ENV_PATH.touch()
        click.echo(f"Created {GAC_ENV_PATH}")

    success = configure_reasoning_effort_workflow(GAC_ENV_PATH)

    if success:
        click.echo(f"\nConfiguration saved to {GAC_ENV_PATH}")
    else:
        click.echo("\nReasoning effort configuration cancelled.")
