"""Reusable bar chart builders and formatting helpers for stats CLI display."""

from collections.abc import Callable
from datetime import datetime
from typing import Any

from rich.table import Table

_PROJECT_MEDALS = ["🥇", "🥈", "🥉"]


def project_rank_label(rank: int, name: str) -> str:
    """Return project name with a medal for top 3, otherwise plain."""
    if rank <= 3:
        return f"{_PROJECT_MEDALS[rank - 1]} {name}"
    return name


def format_latency(ms: int) -> str:
    """Format a latency in milliseconds as a human-readable string.

    Examples: 420ms, 1.2s, 12.5s
    """
    if ms < 1000:
        return f"{ms}ms"
    return f"{ms / 1000:.1f}s"


def format_tps(output_tokens: int, reasoning_tokens: int, duration_ms: int) -> str:
    """Format effective output throughput (tokens/sec) for a single gac.

    Effective TPS = (output_tokens + reasoning_tokens) / wall-clock seconds.
    Prompt tokens are excluded — they measure input size, not generation speed.
    Returns '\u2014' when duration is missing or zero.
    """
    if duration_ms <= 0:
        return "\u2014"
    generated = output_tokens + reasoning_tokens
    if generated <= 0:
        return "\u2014"
    tps = generated * 1000 / duration_ms
    if tps >= 100:
        return f"{tps:,.0f} tps"
    return f"{tps:.1f} tps"


def format_tps_value(tps: int | float | None) -> str:
    """Format a single tps value for display (no unit suffix)."""
    if tps is None:
        return ""
    if tps >= 100:
        return f"{tps:,.0f}"
    return f"{tps:.1f}"


def format_speed_pair(all_time_tps: int | float | None, recent_tps: int | float | None) -> str:
    """Format all-time vs recent speed as '200 / 150 tps' or just '200 tps'.

    Shows both values only when they format differently — if they render
    the same string, the difference is too small to matter for display.
    """
    all_str = format_tps_value(all_time_tps)
    recent_str = format_tps_value(recent_tps)
    if not all_str and not recent_str:
        return "\u2014"
    if not all_str:
        return f"{recent_str} tps"
    if recent_tps is None:
        return f"{all_str} tps"
    if recent_str != all_str:
        return f"{all_str} / {recent_str} tps"
    return f"{all_str} tps"


def format_latency_pair(all_time_ms: int | None, recent_ms: int | None) -> str:
    """Format all-time vs recent latency as '4.2 / 5.1s' or just '4.2s'.

    Shows both values only when they format differently — if they render
    the same string, the difference is too small to matter for display.
    """
    if all_time_ms is None and recent_ms is None:
        return "\u2014"
    if all_time_ms is None:
        return format_latency(recent_ms or 0) if recent_ms is not None else "\u2014"
    if recent_ms is None:
        return format_latency(all_time_ms)
    all_str = format_latency(all_time_ms)
    rec_str = format_latency(recent_ms)
    if rec_str != all_str:
        return f"{all_str} / {rec_str}"
    return all_str


def format_relative_time(iso_ts: str) -> str:
    """Format an ISO timestamp as a human-readable relative time string."""
    try:
        ts = datetime.fromisoformat(iso_ts)
        delta = datetime.now() - ts
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "just now"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"
        days = hours // 24
        if days == 1:
            return "yesterday"
        if days < 30:
            return f"{days}d ago"
        return ts.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return "\u2014"


def build_bar_chart(
    items: list[tuple[str, dict[str, Any]]],
    value_key: str,
    max_value: float,
    label_fmt: Callable[[int], str],
    higher_is_better: bool = True,
    max_bar_width: int = 30,
    item_label_fmt: Callable[[str, dict[str, Any], int], str] | None = None,
) -> Table:
    """Build a horizontal bar chart table for any stat metric.

    Args:
        items: List of (name, data_dict) tuples, pre-sorted.
        value_key: Key in data_dict for the chart value (e.g. 'avg_tps', 'gacs').
        max_value: Maximum value in the dataset (for ratio calculation).
        label_fmt: Callable to format the value for the right column label.
        higher_is_better: If True, high values get bright colors (speed).
            If False, low values get bright colors (latency).
        max_bar_width: Maximum bar width in characters.
        item_label_fmt: Optional callable (name, data, rank) -> label str.
            If None, the raw name is used.

    Returns:
        A Rich Table with Item, Bar, and Value columns.
    """
    table = Table(show_header=False, box=None, padding=(0, 0))
    table.add_column("Item", style="bold magenta", min_width=16, no_wrap=True)
    table.add_column("Bar", ratio=1)
    table.add_column("Value", style="bold cyan", justify="right", min_width=8)

    sub_chars = " ▏▎▍▌▋▊▉█"

    for rank, (item_name, data) in enumerate(items, 1):
        value = data[value_key]
        ratio = value / max_value if max_value > 0 else 0

        full_width = ratio * max_bar_width
        full_blocks = int(full_width)
        if full_blocks >= max_bar_width:
            bar_str = "█" * max_bar_width
        else:
            frac = full_width - full_blocks
            # Only add a fractional block when there is a remainder; otherwise keep bars exact.
            sub_idx = min(int(frac * 8), 7) if frac > 0 else 0
            bar_str = "█" * full_blocks + sub_chars[sub_idx]
            bar_str = bar_str.ljust(max_bar_width)

        if higher_is_better:
            if ratio >= 0.75:
                color = "bold yellow"
            elif ratio >= 0.5:
                color = "green"
            elif ratio >= 0.25:
                color = "cyan"
            else:
                color = "dim cyan"
        else:
            if ratio <= 0.25:
                color = "bold yellow"
            elif ratio <= 0.5:
                color = "green"
            elif ratio <= 0.75:
                color = "cyan"
            else:
                color = "dim red"

        if item_label_fmt:
            label = item_label_fmt(item_name, data, rank)
        else:
            label = item_name

        table.add_row(label, f"[{color}]{bar_str}[/]", label_fmt(value))

    return table
