"""Tests for per-gac history tracking (schema v4) and gac stats recent command."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from gac.cli import cli
from gac.stats.migration import HISTORY_CAP
from gac.stats.recorder import TokenAccumulator
from gac.stats.store import _empty_stats, append_history


class TestTokenAccumulatorExtended:
    """Tests for the extended TokenAccumulator with per-gac metadata."""

    def test_add_tokens(self) -> None:
        acc = TokenAccumulator()
        acc.add_tokens(100, 50, 10, duration_ms=2000)
        assert acc._prompt_tokens == 100
        assert acc._output_tokens == 50
        assert acc._reasoning_tokens == 10
        assert acc._duration_ms == 2000
        assert acc.current == 160

    def test_add_commit(self) -> None:
        acc = TokenAccumulator()
        acc.add_commit()
        acc.add_commit()
        assert acc._commits == 2

    def test_set_meta(self) -> None:
        acc = TokenAccumulator()
        acc.set_meta("openai:gpt-4o", "my-proj")
        assert acc._model == "openai:gpt-4o"
        assert acc._project == "my-proj"
        assert acc._started_at is not None

    def test_set_meta_first_wins_for_started_at(self) -> None:
        acc = TokenAccumulator()
        acc.set_meta("model-a", "proj-a")
        first = acc._started_at
        acc.set_meta("model-b", "proj-b")
        assert acc._started_at == first  # doesn't change

    def test_has_data_with_tokens(self) -> None:
        acc = TokenAccumulator()
        acc.add_tokens(100, 50, 0)
        assert acc.has_data is True

    def test_has_data_with_commits_only(self) -> None:
        acc = TokenAccumulator()
        acc.add_commit()
        assert acc.has_data is True

    def test_has_data_empty(self) -> None:
        acc = TokenAccumulator()
        assert acc.has_data is False

    def test_reset_clears_all_fields(self) -> None:
        acc = TokenAccumulator()
        acc.add_tokens(100, 50, 10, duration_ms=2000)
        acc.add_commit()
        acc.set_meta("model", "project")
        acc.reset()
        assert acc._prompt_tokens == 0
        assert acc._output_tokens == 0
        assert acc._reasoning_tokens == 0
        assert acc._duration_ms == 0
        assert acc._commits == 0
        assert acc._model is None
        assert acc._project is None
        assert acc._started_at is None
        assert acc.current == 0


class TestAppendHistory:
    """Tests for the append_history ring buffer helper."""

    def test_append_first_record(self) -> None:
        stats = _empty_stats()
        record = {"ts": "2025-05-25T10:00:00", "project": "gac", "model": "test"}
        append_history(stats, record)
        assert len(stats["history"]) == 1
        assert stats["history"][0] == record

    def test_append_trims_at_cap(self) -> None:
        stats = _empty_stats()
        # Fill up to cap + 1
        for i in range(HISTORY_CAP + 1):
            append_history(stats, {"ts": f"record-{i}", "idx": i})
        # Should be exactly HISTORY_CAP
        assert len(stats["history"]) == HISTORY_CAP
        # Oldest should have been dropped (record-0 is gone)
        assert stats["history"][0]["idx"] == 1
        # Newest should be at the end
        assert stats["history"][-1]["idx"] == HISTORY_CAP


class TestSchemaV4Migration:
    """Tests for v3→v4 migration (adds empty history)."""

    def test_v3_to_v4_adds_history(self) -> None:
        from gac.stats.migration import _migrate_v3_to_v4

        v3_data = {"_version": 3, "total_gacs": 5}
        result = _migrate_v3_to_v4(v3_data)
        assert result["_version"] == 4
        assert "history" in result
        assert result["history"] == []

    def test_v4_idempotent(self) -> None:
        from gac.stats.migration import _migrate_v3_to_v4

        v4_data = {"_version": 4, "history": [{"ts": "existing"}]}
        result = _migrate_v3_to_v4(v4_data)
        assert result["_version"] == 4
        assert len(result["history"]) == 1  # untouched


class TestStatsRecentCommand:
    """Tests for the 'gac stats recent' subcommand."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_recent_no_history(self, runner) -> None:
        with patch("gac.stats.commands.load_stats", return_value={"history": []}):
            result = runner.invoke(cli, ["stats", "recent"])
            assert result.exit_code == 0
            assert "No gac history yet" in result.output

    def test_recent_with_history(self, runner) -> None:
        now = datetime.now()
        data = {
            "history": [
                {
                    "ts": (now - timedelta(hours=1)).isoformat(),
                    "project": "gac",
                    "model": "anthropic:claude-sonnet-4",
                    "prompt_tokens": 1500,
                    "output_tokens": 600,
                    "reasoning_tokens": 200,
                    "duration_ms": 4200,
                    "commits": 2,
                },
                {
                    "ts": (now - timedelta(minutes=30)).isoformat(),
                    "project": "web-app",
                    "model": "openai:gpt-4o",
                    "prompt_tokens": 2000,
                    "output_tokens": 800,
                    "reasoning_tokens": 0,
                    "duration_ms": 3100,
                    "commits": 1,
                },
            ]
        }
        with patch("gac.stats.commands.load_stats", return_value=data):
            result = runner.invoke(cli, ["stats", "recent"])
            assert result.exit_code == 0
            assert "Recent Gacs" in result.output
            assert "gac" in result.output
            assert "web-app" in result.output
            assert "anthropic:claude-sonnet-4" in result.output

    def test_recent_with_n_flag(self, runner) -> None:
        now = datetime.now()
        history = [
            {
                "ts": (now - timedelta(hours=i)).isoformat(),
                "project": f"proj-{i}",
                "model": "test-model",
                "prompt_tokens": 100,
                "output_tokens": 50,
                "reasoning_tokens": 0,
                "duration_ms": 1000,
                "commits": 1,
            }
            for i in range(20)
        ]
        with patch("gac.stats.commands.load_stats", return_value={"history": history}):
            result = runner.invoke(cli, ["stats", "recent", "-n", "5"])
            assert result.exit_code == 0
            assert "Last 5 gacs" in result.output

    def test_recent_shows_relative_times(self, runner) -> None:
        now = datetime.now()
        data = {
            "history": [
                {
                    "ts": (now - timedelta(minutes=5)).isoformat(),
                    "project": "gac",
                    "model": "test",
                    "prompt_tokens": 100,
                    "output_tokens": 50,
                    "reasoning_tokens": 0,
                    "duration_ms": 1000,
                    "commits": 1,
                },
            ]
        }
        with patch("gac.stats.commands.load_stats", return_value=data):
            result = runner.invoke(cli, ["stats", "recent"])
            assert result.exit_code == 0
            assert "5m" in result.output

    def test_recent_stats_disabled(self, runner) -> None:
        with patch("gac.stats.commands.stats_enabled", return_value=False):
            result = runner.invoke(cli, ["stats", "recent"])
            assert result.exit_code == 0
            assert "disabled" in result.output.lower()


class TestFormatRelativeTime:
    """Tests for the _format_relative_time helper."""

    def test_just_now(self) -> None:
        from gac.stats.charts import format_relative_time

        ts = (datetime.now() - timedelta(seconds=30)).isoformat()
        assert format_relative_time(ts) == "just now"

    def test_minutes_ago(self) -> None:
        from gac.stats.charts import format_relative_time

        ts = (datetime.now() - timedelta(minutes=15)).isoformat()
        assert format_relative_time(ts) == "15m ago"

    def test_hours_ago(self) -> None:
        from gac.stats.charts import format_relative_time

        ts = (datetime.now() - timedelta(hours=3)).isoformat()
        assert format_relative_time(ts) == "3h ago"

    def test_yesterday(self) -> None:
        from gac.stats.charts import format_relative_time

        ts = (datetime.now() - timedelta(hours=25)).isoformat()
        assert format_relative_time(ts) == "yesterday"

    def test_days_ago(self) -> None:
        from gac.stats.charts import format_relative_time

        ts = (datetime.now() - timedelta(days=5)).isoformat()
        assert format_relative_time(ts) == "5d ago"

    def test_old_date_shows_date(self) -> None:
        from gac.stats.charts import format_relative_time

        ts = (datetime.now() - timedelta(days=60)).isoformat()
        result = format_relative_time(ts)
        # Should show YYYY-MM-DD format for old dates
        assert "-" in result
        assert result != "60d ago"

    def test_invalid_timestamp(self) -> None:
        from gac.stats.charts import format_relative_time

        assert format_relative_time("not-a-date") == "\u2014"
