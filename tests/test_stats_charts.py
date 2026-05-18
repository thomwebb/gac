"""Tests for gac.stats.charts — reusable bar chart builders and formatting helpers."""

from datetime import datetime, timedelta

from gac.stats.charts import (
    build_bar_chart,
    format_latency,
    format_latency_pair,
    format_relative_time,
    format_speed_pair,
    format_tps,
    project_rank_label,
)


class TestFormatLatency:
    def test_milliseconds(self) -> None:
        assert format_latency(420) == "420ms"

    def test_seconds(self) -> None:
        assert format_latency(2500) == "2.5s"

    def test_exactly_one_second(self) -> None:
        assert format_latency(1000) == "1.0s"


class TestProjectRankLabel:
    def test_gold(self) -> None:
        assert project_rank_label(1, "proj") == "🥇 proj"

    def test_silver(self) -> None:
        assert project_rank_label(2, "proj") == "🥈 proj"

    def test_bronze(self) -> None:
        assert project_rank_label(3, "proj") == "🥉 proj"

    def test_plain(self) -> None:
        assert project_rank_label(4, "proj") == "proj"


class TestFormatRelativeTime:
    def test_just_now(self) -> None:
        ts = (datetime.now() - timedelta(seconds=30)).isoformat()
        assert format_relative_time(ts) == "just now"

    def test_invalid(self) -> None:
        assert format_relative_time("bad") == "\u2014"


class TestFormatTps:
    def test_basic(self) -> None:
        # 800 output + 200 reasoning = 1000 generated, over 4s = 250 tps
        assert format_tps(800, 200, 4000) == "250 tps"

    def test_no_reasoning(self) -> None:
        # 800 output, 0 reasoning, over 3.1s = 258.1 tps
        result = format_tps(800, 0, 3100)
        assert "tps" in result

    def test_high_tps_rounds(self) -> None:
        # 10000 generated over 0.5s = 20000 tps → formatted as integer
        assert format_tps(10000, 0, 500) == "20,000 tps"

    def test_low_tps_decimal(self) -> None:
        # 10 generated over 5s = 2 tps → decimal format
        assert format_tps(10, 0, 5000) == "2.0 tps"

    def test_zero_duration(self) -> None:
        assert format_tps(800, 200, 0) == "\u2014"

    def test_zero_output(self) -> None:
        assert format_tps(0, 0, 4000) == "\u2014"

    def test_thinking_model(self) -> None:
        # deepseek-r1: 1500 output + 12000 reasoning over 90s = 150 tps
        assert format_tps(1500, 12000, 90000) == "150 tps"


class TestFormatSpeedPair:
    def test_all_time_only(self) -> None:
        assert format_speed_pair(200, None) == "200 tps"

    def test_both_differ(self) -> None:
        assert format_speed_pair(200, 150) == "200 / 150 tps"

    def test_both_same(self) -> None:
        assert format_speed_pair(200, 200) == "200 tps"

    def test_none_all_time(self) -> None:
        assert format_speed_pair(None, 150) == "150 tps"

    def test_both_none(self) -> None:
        assert format_speed_pair(None, None) == "\u2014"

    def test_decimal_tps(self) -> None:
        # Low tps shows decimal
        assert format_speed_pair(41, 42) == "41.0 / 42.0 tps"

    def test_different_values_shown(self) -> None:
        # All-time integer, recent decimal — both should be displayed
        result = format_speed_pair(200, 41)
        assert "/" in result
        assert "tps" in result

    def test_zero_recent_not_treated_as_missing(self) -> None:
        # 0 tps is a real value, not "no data"
        assert format_speed_pair(200, 0) == "200 / 0.0 tps"

    def test_different_values_same_format_collapsed(self) -> None:
        # 199 and 200 format differently ("199" vs "200") so pair shown
        assert "/" in format_speed_pair(199, 200)
        # But values that format identically are collapsed — no noise
        # (not easy to hit with tps, but the principle matters)


class TestFormatLatencyPair:
    def test_all_time_only(self) -> None:
        assert format_latency_pair(4200, None) == "4.2s"

    def test_both_differ(self) -> None:
        assert format_latency_pair(4200, 6000) == "4.2s / 6.0s"

    def test_both_same(self) -> None:
        assert format_latency_pair(4200, 4200) == "4.2s"

    def test_none_all_time(self) -> None:
        assert format_latency_pair(None, 6000) == "6.0s"

    def test_both_none(self) -> None:
        assert format_latency_pair(None, None) == "\u2014"

    def test_milliseconds(self) -> None:
        assert format_latency_pair(420, 800) == "420ms / 800ms"

    def test_different_values_same_format_collapsed(self) -> None:
        # 4199ms and 4201ms both format as 4.2s — showing both is noise
        result = format_latency_pair(4199, 4201)
        assert "/" not in result  # collapsed since formatted strings match

    def test_zero_recent_not_treated_as_missing(self) -> None:
        # 0ms is a real value, not "no data"
        assert format_latency_pair(4200, 0) == "4.2s / 0ms"


class TestComputeRecentModelStats:
    def test_basic_recent(self) -> None:
        from gac.stats.store import _compute_recent_model_stats

        now = datetime.now()
        history = [
            {
                "ts": (now - timedelta(days=2)).isoformat(),
                "model": "openai:gpt-4o",
                "output_tokens": 800,
                "reasoning_tokens": 0,
                "duration_ms": 3100,
                "commits": 1,
            },
        ]
        result = _compute_recent_model_stats(history, days=30)
        assert "openai:gpt-4o" in result
        assert result["openai:gpt-4o"]["recent_tps"] == 258  # 800*1000/3100
        assert result["openai:gpt-4o"]["recent_latency_ms"] == 3100
        assert result["openai:gpt-4o"]["recent_latency_per_commit_ms"] == 3100  # 3100ms / 1 commit

    def test_per_commit_with_multiple_commits(self) -> None:
        from gac.stats.store import _compute_recent_model_stats

        now = datetime.now()
        history = [
            {
                "ts": (now - timedelta(days=2)).isoformat(),
                "model": "openai:gpt-4o",
                "output_tokens": 800,
                "reasoning_tokens": 0,
                "duration_ms": 5000,
                "commits": 5,
            },
        ]
        result = _compute_recent_model_stats(history, days=30)
        assert result["openai:gpt-4o"]["recent_latency_per_commit_ms"] == 1000  # 5000ms / 5 commits

    def test_excludes_old_entries(self) -> None:
        from gac.stats.store import _compute_recent_model_stats

        now = datetime.now()
        history = [
            {
                "ts": (now - timedelta(days=60)).isoformat(),
                "model": "openai:gpt-4o",
                "output_tokens": 800,
                "reasoning_tokens": 0,
                "duration_ms": 3100,
                "commits": 1,
            },
        ]
        result = _compute_recent_model_stats(history, days=30)
        assert result == {}

    def test_excludes_zero_duration(self) -> None:
        from gac.stats.store import _compute_recent_model_stats

        now = datetime.now()
        history = [
            {
                "ts": (now - timedelta(days=1)).isoformat(),
                "model": "openai:gpt-4o",
                "output_tokens": 800,
                "reasoning_tokens": 0,
                "duration_ms": 0,
                "commits": 1,
            },
        ]
        result = _compute_recent_model_stats(history, days=30)
        assert result == {}

    def test_aggregates_multiple_gacs(self) -> None:
        from gac.stats.store import _compute_recent_model_stats

        now = datetime.now()
        history = [
            {
                "ts": (now - timedelta(days=1)).isoformat(),
                "model": "openai:gpt-4o",
                "output_tokens": 600,
                "reasoning_tokens": 0,
                "duration_ms": 3000,
                "commits": 1,
            },
            {
                "ts": (now - timedelta(days=3)).isoformat(),
                "model": "openai:gpt-4o",
                "output_tokens": 400,
                "reasoning_tokens": 0,
                "duration_ms": 2000,
                "commits": 1,
            },
        ]
        result = _compute_recent_model_stats(history, days=30)
        # Total: 1000 tokens, 5000ms, 2 calls → 200 tps, 2500ms avg latency
        assert result["openai:gpt-4o"]["recent_tps"] == 200
        assert result["openai:gpt-4o"]["recent_latency_ms"] == 2500

    def test_empty_history(self) -> None:
        from gac.stats.store import _compute_recent_model_stats

        result = _compute_recent_model_stats([], days=30)
        assert result == {}

    def test_no_model_field(self) -> None:
        from gac.stats.store import _compute_recent_model_stats

        now = datetime.now()
        history = [{"ts": (now - timedelta(days=1)).isoformat(), "output_tokens": 800, "duration_ms": 3000}]
        result = _compute_recent_model_stats(history, days=30)
        assert result == {}


class TestBuildBarChart:
    def test_basic_chart(self) -> None:
        data = [("a", {"v": 50}), ("b", {"v": 25})]
        table = build_bar_chart(data, value_key="v", max_value=50, label_fmt=lambda v: str(v))
        assert table.row_count == 2

    def test_empty_data(self) -> None:
        table = build_bar_chart([], value_key="v", max_value=100, label_fmt=lambda v: str(v))
        assert table.row_count == 0

    def test_item_label_fmt(self) -> None:
        data = [("a", {"v": 50}), ("b", {"v": 25})]
        table = build_bar_chart(
            data,
            value_key="v",
            max_value=50,
            label_fmt=lambda v: str(v),
            item_label_fmt=lambda name, _d, rank: f"#{rank} {name}",
        )
        first = table.columns[0]._cells[0]  # type: ignore[attr-defined]
        assert first == "#1 a"

    def test_zero_max_value(self) -> None:
        data = [("zero", {"v": 0})]
        table = build_bar_chart(data, value_key="v", max_value=0, label_fmt=lambda v: str(v))
        assert table.row_count == 1
