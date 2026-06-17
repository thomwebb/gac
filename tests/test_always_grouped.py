"""Tests for the always grouped feature."""

from unittest.mock import patch

import pytest

from gac.config import load_config


class TestAlwaysGroupedConfig:
    """Test the always_grouped configuration option."""

    def test_default_always_grouped_false(self, monkeypatch):
        """Test that always_grouped defaults to False."""
        monkeypatch.setenv("GAC_ALWAYS_GROUPED", "")
        monkeypatch.delenv("GAC_ALWAYS_GROUPED", raising=False)

        config = load_config()
        assert config["always_grouped"] is False

    @pytest.mark.parametrize(
        "env_value,expected",
        [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("YES", True),
            ("on", True),
            ("ON", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("NO", False),
            ("off", False),
            ("OFF", False),
            ("anything_else", False),
            ("", False),
        ],
    )
    def test_always_grouped_env_values(self, monkeypatch, env_value, expected):
        """Test various environment variable values for always_grouped."""
        monkeypatch.setenv("GAC_ALWAYS_GROUPED", env_value)

        config = load_config()
        assert config["always_grouped"] is expected


class TestAlwaysGroupedCLI:
    """Test the CLI behavior with always_grouped setting."""

    @patch("gac.cli.main")
    def test_cli_applies_always_grouped_when_enabled(self, mock_main, monkeypatch):
        """Test that CLI applies grouped mode when always_grouped is enabled and no -g flag is used."""
        from click.testing import CliRunner

        from gac.cli import cli

        # Mock the config to return always_grouped=True
        mock_config = {
            "log_level": "ERROR",
            "model": "test:model",
            "always_include_scope": False,
            "always_grouped": True,
            "no_verify_ssl": False,
            "verbose": False,
            "skip_secret_scan": False,
            "hook_timeout": 120,
            "use_50_72_rule": False,
            "signoff": False,
        }
        monkeypatch.setattr("gac.config.load_config", lambda: mock_config)
        mock_main.return_value = 0

        runner = CliRunner()
        runner.invoke(cli, [])

        # Check that main was called with group=True (which triggers grouped mode)
        mock_main.assert_called_once()
        opts = mock_main.call_args[0][0]  # First positional arg is CLIOptions
        assert opts.group is True

    @patch("gac.cli.main")
    def test_cli_uses_group_flag_when_provided(self, mock_main, monkeypatch):
        """Test that -g flag triggers grouped mode when provided."""
        from click.testing import CliRunner

        from gac.cli import cli

        # Mock the config to return always_grouped=False
        mock_config = {
            "log_level": "ERROR",
            "model": "test:model",
            "always_include_scope": False,
            "always_grouped": False,
            "no_verify_ssl": False,
            "verbose": False,
            "skip_secret_scan": False,
            "hook_timeout": 120,
            "use_50_72_rule": False,
            "signoff": False,
        }
        monkeypatch.setattr("gac.config.load_config", lambda: mock_config)
        mock_main.return_value = 0

        runner = CliRunner()
        runner.invoke(cli, ["-g"])

        # Check that main was called with group=True
        mock_main.assert_called_once()
        opts = mock_main.call_args[0][0]  # First positional arg is CLIOptions
        assert opts.group is True

    @patch("gac.cli.main")
    def test_cli_does_not_apply_grouped_when_disabled(self, mock_main, monkeypatch):
        """Test that CLI does not apply grouped mode when always_grouped is disabled."""
        from click.testing import CliRunner

        from gac.cli import cli

        # Mock the config to return always_grouped=False
        mock_config = {
            "log_level": "ERROR",
            "model": "test:model",
            "always_include_scope": False,
            "always_grouped": False,
            "no_verify_ssl": False,
            "verbose": False,
            "skip_secret_scan": False,
            "hook_timeout": 120,
            "use_50_72_rule": False,
            "signoff": False,
        }
        monkeypatch.setattr("gac.config.load_config", lambda: mock_config)
        mock_main.return_value = 0

        runner = CliRunner()
        runner.invoke(cli, [])

        # Check that main was called with group=False (no grouping)
        mock_main.assert_called_once()
        opts = mock_main.call_args[0][0]  # First positional arg is CLIOptions
        assert opts.group is False

    @patch("gac.cli.main")
    def test_cli_group_flag_overrides_config(self, mock_main, monkeypatch):
        """Test that -g flag takes precedence over always_grouped setting."""
        from click.testing import CliRunner

        from gac.cli import cli

        # Mock the config to return always_grouped=False
        mock_config = {
            "log_level": "ERROR",
            "model": "test:model",
            "always_include_scope": False,
            "always_grouped": False,  # Config says false
            "no_verify_ssl": False,
            "verbose": False,
            "skip_secret_scan": False,
            "hook_timeout": 120,
            "use_50_72_rule": False,
            "signoff": False,
        }
        monkeypatch.setattr("gac.config.load_config", lambda: mock_config)
        mock_main.return_value = 0

        runner = CliRunner()
        runner.invoke(cli, ["-g"])  # But flag says true

        # Check that main was called with group=True (flag overrides config)
        mock_main.assert_called_once()
        opts = mock_main.call_args[0][0]  # First positional arg is CLIOptions
        assert opts.group is True


class TestAlwaysGroupedMutualExclusion:
    """Test mutual exclusion between always_grouped and --message-only."""

    @patch("gac.cli.main")
    def test_config_grouped_with_message_only_rejected(self, mock_main, monkeypatch):
        """Test that --message-only is rejected when always_grouped is enabled via config."""
        from click.testing import CliRunner

        from gac.cli import cli

        # Mock the config to return always_grouped=True
        mock_config = {
            "log_level": "ERROR",
            "model": "test:model",
            "always_include_scope": False,
            "always_grouped": True,  # Config enables grouping
            "no_verify_ssl": False,
            "verbose": False,
            "skip_secret_scan": False,
            "hook_timeout": 120,
            "use_50_72_rule": False,
            "signoff": False,
        }
        monkeypatch.setattr("gac.config.load_config", lambda: mock_config)

        runner = CliRunner()
        result = runner.invoke(cli, ["--message-only"])

        # Should exit with error
        assert result.exit_code == 1
        assert "Error: --message-only and --group options are mutually exclusive" in result.output

    @patch("gac.cli.main")
    def test_explicit_group_flag_with_message_only_rejected(self, mock_main, monkeypatch):
        """Test that --message-only is rejected when --group flag is explicitly provided."""
        from click.testing import CliRunner

        from gac.cli import cli

        # Mock the config with always_grouped=False
        mock_config = {
            "log_level": "ERROR",
            "model": "test:model",
            "always_include_scope": False,
            "always_grouped": False,
            "no_verify_ssl": False,
            "verbose": False,
            "skip_secret_scan": False,
            "hook_timeout": 120,
            "use_50_72_rule": False,
            "signoff": False,
        }
        monkeypatch.setattr("gac.config.load_config", lambda: mock_config)

        runner = CliRunner()
        result = runner.invoke(cli, ["--group", "--message-only"])

        # Should exit with error
        assert result.exit_code == 1
        assert "Error: --message-only and --group options are mutually exclusive" in result.output

    @patch("gac.cli.main")
    def test_no_grouping_with_message_only_accepted(self, mock_main, monkeypatch):
        """Test that --message-only is accepted when grouping is disabled."""
        from click.testing import CliRunner

        from gac.cli import cli

        # Mock the config with always_grouped=False
        mock_config = {
            "log_level": "ERROR",
            "model": "test:model",
            "always_include_scope": False,
            "always_grouped": False,
            "no_verify_ssl": False,
            "verbose": False,
            "skip_secret_scan": False,
            "hook_timeout": 120,
            "use_50_72_rule": False,
            "signoff": False,
        }
        monkeypatch.setattr("gac.config.load_config", lambda: mock_config)
        mock_main.return_value = 0

        runner = CliRunner()
        result = runner.invoke(cli, ["--message-only"])

        # Should succeed (main gets called)
        assert result.exit_code == 0
        mock_main.assert_called_once()
        opts = mock_main.call_args[0][0]  # First positional arg is CLIOptions
        assert opts.message_only is True
        assert opts.group is False
