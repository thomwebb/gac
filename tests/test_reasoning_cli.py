"""Tests for reasoning_cli module — configure_reasoning_effort_workflow and reasoning CLI command."""

import tempfile
from pathlib import Path
from unittest import mock

from click.testing import CliRunner
from dotenv import dotenv_values

from gac.reasoning_cli import configure_reasoning_effort_workflow, reasoning

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_env(tmpdir: str, content: str = "") -> Path:
    """Create a .gac.env in tmpdir with the given content and return its path."""
    env_path = Path(tmpdir) / ".gac.env"
    env_path.write_text(content)
    return env_path


def _read_env(env_path: Path) -> dict[str, str | None]:
    """Read the env file via dotenv_values — single consistent assertion pathway."""
    return dict(dotenv_values(str(env_path)))


# ===================================================================
# Tests for configure_reasoning_effort_workflow
# ===================================================================

# --- Branch: No existing value ----------------------------------------


def test_no_existing_value_skip():
    """No existing value → select Skip (use model default)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _make_env(tmpdir)
        with mock.patch("questionary.select") as mselect:
            mselect.return_value.ask.return_value = "Skip (use model default)"
            result = configure_reasoning_effort_workflow(env_path)
        assert result is True
        assert "GAC_REASONING_EFFORT" not in _read_env(env_path)


def test_no_existing_value_none():
    """No existing value → select none."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _make_env(tmpdir)
        with mock.patch("questionary.select") as mselect:
            mselect.return_value.ask.return_value = "none"
            result = configure_reasoning_effort_workflow(env_path)
        assert result is True
        assert _read_env(env_path).get("GAC_REASONING_EFFORT") == "none"


def test_no_existing_value_low():
    """No existing value → select low."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _make_env(tmpdir)
        with mock.patch("questionary.select") as mselect:
            mselect.return_value.ask.return_value = "low"
            result = configure_reasoning_effort_workflow(env_path)
        assert result is True
        assert _read_env(env_path).get("GAC_REASONING_EFFORT") == "low"


def test_no_existing_value_medium():
    """No existing value → select medium."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _make_env(tmpdir)
        with mock.patch("questionary.select") as mselect:
            mselect.return_value.ask.return_value = "medium"
            result = configure_reasoning_effort_workflow(env_path)
        assert result is True
        assert _read_env(env_path).get("GAC_REASONING_EFFORT") == "medium"


def test_no_existing_value_high():
    """No existing value → select high."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _make_env(tmpdir)
        with mock.patch("questionary.select") as mselect:
            mselect.return_value.ask.return_value = "high"
            result = configure_reasoning_effort_workflow(env_path)
        assert result is True
        assert _read_env(env_path).get("GAC_REASONING_EFFORT") == "high"


def test_no_existing_value_max():
    """No existing value → select max."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _make_env(tmpdir)
        with mock.patch("questionary.select") as mselect:
            mselect.return_value.ask.return_value = "max"
            result = configure_reasoning_effort_workflow(env_path)
        assert result is True
        assert _read_env(env_path).get("GAC_REASONING_EFFORT") == "max"


def test_no_existing_value_cancel():
    """No existing value → cancel (None) at full choice list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _make_env(tmpdir)
        with mock.patch("questionary.select") as mselect:
            mselect.return_value.ask.return_value = None
            result = configure_reasoning_effort_workflow(env_path)
        assert result is True
        assert "GAC_REASONING_EFFORT" not in _read_env(env_path)


# --- Branch: Existing valid value -------------------------------------


def test_existing_valid_keep():
    """Existing valid value → Keep existing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _make_env(tmpdir, "GAC_REASONING_EFFORT=low\n")
        with mock.patch("questionary.select") as mselect:
            mselect.return_value.ask.return_value = "Keep existing (low)"
            result = configure_reasoning_effort_workflow(env_path)
        assert result is True
        assert _read_env(env_path).get("GAC_REASONING_EFFORT") == "low"


def test_existing_valid_select_new_high():
    """Existing valid value → Select new value → pick high."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _make_env(tmpdir, "GAC_REASONING_EFFORT=low\n")
        with mock.patch("questionary.select") as mselect:
            # First call: "How would you like to proceed?" → "Select new value"
            # Second call: "Select reasoning effort:" → "high"
            mselect.return_value.ask.side_effect = ["Select new value", "high"]
            result = configure_reasoning_effort_workflow(env_path)
        assert result is True
        assert _read_env(env_path).get("GAC_REASONING_EFFORT") == "high"


def test_existing_valid_disable():
    """Existing valid value → Disable (use model default)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _make_env(tmpdir, "GAC_REASONING_EFFORT=medium\n")
        with mock.patch("questionary.select") as mselect:
            mselect.return_value.ask.return_value = "Disable (use model default)"
            result = configure_reasoning_effort_workflow(env_path)
        assert result is True
        assert "GAC_REASONING_EFFORT" not in _read_env(env_path)


def test_existing_valid_cancel_at_proceed():
    """Existing valid value → cancel (None) at 'How would you like to proceed?'."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _make_env(tmpdir, "GAC_REASONING_EFFORT=medium\n")
        with mock.patch("questionary.select") as mselect:
            mselect.return_value.ask.return_value = None
            result = configure_reasoning_effort_workflow(env_path)
        assert result is True
        assert _read_env(env_path).get("GAC_REASONING_EFFORT") == "medium"


# --- Branch: Existing invalid value -----------------------------------


def test_existing_invalid_select_new_low():
    """Existing invalid value → Select new value → pick low."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _make_env(tmpdir, "GAC_REASONING_EFFORT=extreme\n")
        with mock.patch("questionary.select") as mselect:
            # First call: "How would you like to proceed?" → "Select new value"
            # Second call: "Select reasoning effort:" → "low"
            mselect.return_value.ask.side_effect = ["Select new value", "low"]
            result = configure_reasoning_effort_workflow(env_path)
        assert result is True
        assert _read_env(env_path).get("GAC_REASONING_EFFORT") == "low"


def test_existing_invalid_disable():
    """Existing invalid value → Disable (use model default)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = _make_env(tmpdir, "GAC_REASONING_EFFORT=extreme\n")
        with mock.patch("questionary.select") as mselect:
            mselect.return_value.ask.return_value = "Disable (use model default)"
            result = configure_reasoning_effort_workflow(env_path)
        assert result is True
        assert "GAC_REASONING_EFFORT" not in _read_env(env_path)


# --- Edge case: whitespace normalization --------------------------------


def test_existing_value_whitespace_normalized():
    """Existing value with extra whitespace is normalized correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write a value with surrounding whitespace
        env_path = _make_env(tmpdir, 'GAC_REASONING_EFFORT="  HIGH  "\n')
        with mock.patch("questionary.select") as mselect:
            # The normalized value is "high", so "Keep existing (high)" should be offered
            mselect.return_value.ask.return_value = "Keep existing (high)"
            result = configure_reasoning_effort_workflow(env_path)
        assert result is True


# ===================================================================
# Tests for the `reasoning` CLI command
# ===================================================================


def test_reasoning_cli_env_file_exists():
    """Env file already exists → workflow succeeds, shows saved message."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_env = Path(tmpdir) / ".gac.env"
        fake_env.touch()
        with (
            mock.patch("gac.reasoning_cli.GAC_ENV_PATH", fake_env),
            mock.patch("gac.reasoning_cli.configure_reasoning_effort_workflow", return_value=True),
        ):
            result = runner.invoke(reasoning)
            assert result.exit_code == 0
            assert "Configuration saved" in result.output
            assert "Created" not in result.output  # File already existed


def test_reasoning_cli_env_file_created():
    """Env file does NOT exist → creates it, workflow succeeds."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_env = Path(tmpdir) / ".gac.env"
        # Deliberately do NOT touch the file
        with (
            mock.patch("gac.reasoning_cli.GAC_ENV_PATH", fake_env),
            mock.patch("gac.reasoning_cli.configure_reasoning_effort_workflow", return_value=True),
        ):
            result = runner.invoke(reasoning)
            assert result.exit_code == 0
            assert "Configuration saved" in result.output
            assert "Created" in result.output
            assert fake_env.exists()


def test_reasoning_cli_workflow_returns_false():
    """Workflow returns False → shows cancellation message."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_env = Path(tmpdir) / ".gac.env"
        fake_env.touch()
        with (
            mock.patch("gac.reasoning_cli.GAC_ENV_PATH", fake_env),
            mock.patch("gac.reasoning_cli.configure_reasoning_effort_workflow", return_value=False),
        ):
            result = runner.invoke(reasoning)
            assert result.exit_code == 0
            assert "Reasoning effort configuration cancelled" in result.output
