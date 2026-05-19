"""Stats persistence layer — loading, saving, and migrating usage data."""

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

from gac.stats.migration import _CURRENT_STATS_VERSION, HISTORY_CAP, _migrate, _migrate_stats_file_location

logger = logging.getLogger(__name__)

STATS_FILE = Path.home() / ".gac" / "stats.json"
_LEGACY_STATS_FILE = Path.home() / ".gac_stats.json"

_FALSY_VALUES = {"", "0", "false", "no", "off", "n"}

_DURATION_DEFAULTS: dict[str, int] = {
    "total_duration_ms": 0,
    "duration_count": 0,
    "timed_output_tokens": 0,
    "timed_reasoning_tokens": 0,
    "min_duration_ms": 0,
    "max_duration_ms": 0,
    "reasoning_tokens": 0,
}


# TYPED DICT


class GACStats(TypedDict):
    """TypedDict for GAC usage statistics."""

    total_gacs: int
    total_commits: int
    total_prompt_tokens: int
    total_output_tokens: int  # excludes reasoning
    total_reasoning_tokens: int
    biggest_gac_tokens: int
    biggest_gac_date: str | None
    biggest_gac_commits: int
    biggest_gac_commits_date: str | None
    biggest_gac_files: int
    biggest_gac_files_date: str | None
    first_used: str | None
    last_used: str | None
    daily_gacs: dict[str, int]
    daily_commits: dict[str, int]
    daily_prompt_tokens: dict[str, int]
    daily_output_tokens: dict[str, int]
    daily_reasoning_tokens: dict[str, int]
    weekly_gacs: dict[str, int]  # ISO week e.g. 2026-W18
    weekly_commits: dict[str, int]
    weekly_prompt_tokens: dict[str, int]
    weekly_output_tokens: dict[str, int]
    weekly_reasoning_tokens: dict[str, int]
    projects: dict[str, Any]
    models: dict[str, Any]
    history: list[dict[str, Any]]  # ring buffer capped at HISTORY_CAP
    _version: int


# HELPERS


def _normalize_models(models: dict[str, Any]) -> dict[str, Any]:
    for _name, data in models.items():
        for field, default in _DURATION_DEFAULTS.items():
            data.setdefault(field, default)
        # Backfill: every recorded gac produced at least one commit, so
        # for pre-existing entries without a commits key, gacs is the
        # best conservative floor (better than 0 for models with 100+ gacs).
        if "commits" not in data:
            data["commits"] = data.get("gacs", 0)
    return models


def _compute_recent_model_stats(history: list[dict[str, Any]], days: int = 30) -> dict[str, dict[str, Any]]:
    """Compute per-model speed and latency from the last N days of gac history.

    Returns ``{model_name: {"recent_tps": int, "recent_latency_ms": int}}``
    for models with at least one timed gac in the window.
    """
    cutoff = datetime.now().timestamp() - days * 86400
    buckets: dict[str, dict[str, int]] = {}  # model -> {output, reasoning, duration_ms, commits, count}
    for gac in history:
        ts = gac.get("ts", "")
        try:
            gac_time = datetime.fromisoformat(ts).timestamp()
        except (ValueError, TypeError):
            continue
        if gac_time < cutoff:
            continue
        model = gac.get("model")
        if not model:
            continue
        duration_ms = gac.get("duration_ms", 0)
        output_t = gac.get("output_tokens", 0)
        reasoning_t = gac.get("reasoning_tokens", 0)
        commits = gac.get("commits", 0)
        if duration_ms <= 0:
            continue
        b = buckets.setdefault(model, {"output": 0, "reasoning": 0, "duration_ms": 0, "commits": 0, "count": 0})
        b["output"] += output_t
        b["reasoning"] += reasoning_t
        b["duration_ms"] += duration_ms
        b["commits"] += max(commits, 1)  # at least 1 commit per gac
        b["count"] += 1

    result: dict[str, dict[str, Any]] = {}
    for model, b in buckets.items():
        if b["duration_ms"] <= 0:
            continue
        generated = b["output"] + b["reasoning"]
        result[model] = {
            "recent_tps": round(generated * 1000 / b["duration_ms"]),
            "recent_latency_ms": round(b["duration_ms"] / b["count"]),
            "recent_latency_per_commit_ms": round(b["duration_ms"] / b["commits"]),
        }
    return result


def _enrich_models_with_speed(
    models: list[tuple[str, Any]], history: list[dict[str, Any]] | None = None, recent_days: int = 30
) -> list[tuple[str, Any]]:
    enriched: list[tuple[str, Any]] = []
    recent = _compute_recent_model_stats(history, recent_days) if history else {}
    for name, data in models:
        avg_tps = None
        avg_latency_ms = None
        avg_latency_per_commit_ms = None
        if data.get("duration_count", 0) > 0 and data.get("total_duration_ms", 0) > 0:
            timed_output = data["timed_output_tokens"] + data.get("timed_reasoning_tokens", 0)
            avg_tps = round(timed_output * 1000 / data["total_duration_ms"])
            avg_latency_ms = round(data["total_duration_ms"] / data["duration_count"])
        commits = data.get("commits", 0)
        total_duration = data.get("total_duration_ms", 0)
        if commits > 0 and total_duration > 0:
            avg_latency_per_commit_ms = round(total_duration / commits)
        r = recent.get(name, {})
        enriched.append(
            (
                name,
                {
                    **data,
                    "avg_tps": avg_tps,
                    "avg_latency_ms": avg_latency_ms,
                    "avg_latency_per_commit_ms": avg_latency_per_commit_ms,
                    "recent_tps": r.get("recent_tps"),
                    "recent_latency_ms": r.get("recent_latency_ms"),
                    "recent_latency_per_commit_ms": r.get("recent_latency_per_commit_ms"),
                },
            )
        )
    return enriched


def _safe_format_date(iso_str: Any) -> str:
    """Format an ISO datetime string to YYYY-MM-DD, returning a safe fallback on failure.

    If the input is not a string or cannot be parsed, returns ``<invalid>`` to
    prevent downstream code from crashing on ``.split("-")`` or similar string ops.
    """
    if not isinstance(iso_str, str):
        return "<invalid>"
    try:
        return datetime.fromisoformat(iso_str).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return "<invalid>"


def stats_enabled() -> bool:
    """Check if stats tracking is enabled.

    Disabled only when GAC_DISABLE_STATS is set to a truthy value
    (e.g. ``true``, ``1``, ``yes``). Falsy values (``false``, ``0``, ``no``,
    ``off``, empty string) leave stats enabled.
    """
    raw = os.environ.get("GAC_DISABLE_STATS")
    if raw is None:
        return True
    return raw.strip().lower() in _FALSY_VALUES


def get_current_project_name() -> str | None:
    """Get the current project name from git remote or directory name.

    Returns:
        Project name (repo name) or None if not in a git repo
    """
    try:
        # Try to get the remote origin URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            remote_url = result.stdout.strip()
            # Extract repo name from URL (handles https:// and git@ formats)
            if "/" in remote_url:
                repo_name = remote_url.split("/")[-1]
                # Remove .git suffix if present
                if repo_name.endswith(".git"):
                    repo_name = repo_name[:-4]
                return repo_name

        # Fallback: get directory name
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            repo_path = result.stdout.strip()
            return Path(repo_path).name
    except (subprocess.SubprocessError, OSError):
        pass

    return None


# LOAD / SAVE / RESET


def _empty_stats() -> GACStats:
    """Return a fresh empty stats dict."""
    return {
        "total_gacs": 0,
        "total_commits": 0,
        "total_prompt_tokens": 0,
        "total_output_tokens": 0,
        "total_reasoning_tokens": 0,
        "biggest_gac_tokens": 0,
        "biggest_gac_date": None,
        "biggest_gac_commits": 0,
        "biggest_gac_commits_date": None,
        "biggest_gac_files": 0,
        "biggest_gac_files_date": None,
        "first_used": None,
        "last_used": None,
        "daily_gacs": {},
        "daily_commits": {},
        "daily_prompt_tokens": {},
        "daily_output_tokens": {},
        "daily_reasoning_tokens": {},
        "weekly_gacs": {},
        "weekly_commits": {},
        "weekly_prompt_tokens": {},
        "weekly_output_tokens": {},
        "weekly_reasoning_tokens": {},
        "projects": {},
        "models": {},
        "history": [],
        "_version": _CURRENT_STATS_VERSION,
    }


def load_stats() -> GACStats:
    """Load statistics from the stats file.

    Returns:
        GACStats dictionary with usage statistics
    """
    _migrate_stats_file_location(stats_file=STATS_FILE, legacy_file=_LEGACY_STATS_FILE)
    empty = _empty_stats()

    if not STATS_FILE.exists():
        return empty

    try:
        with open(STATS_FILE) as f:
            data = json.load(f)

        pre_version = int(data.get("_version", 0))
        data = _migrate(data)
        post_version = int(data.get("_version", _CURRENT_STATS_VERSION))
        if pre_version < post_version:
            try:
                STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
                tmp = STATS_FILE.with_suffix(".tmp")
                with open(tmp, "w") as f:
                    json.dump(data, f, indent=2)
                os.replace(tmp, STATS_FILE)
            except OSError:
                pass  # non-fatal: migration will re-run next time

        return {
            "total_gacs": data.get("total_gacs", 0),
            "total_commits": data.get("total_commits", 0),
            "total_prompt_tokens": data.get("total_prompt_tokens", 0),
            "total_output_tokens": data.get("total_output_tokens", 0),
            "total_reasoning_tokens": data.get("total_reasoning_tokens", 0),
            "biggest_gac_tokens": data.get("biggest_gac_tokens", 0),
            "biggest_gac_date": data.get("biggest_gac_date"),
            "biggest_gac_commits": data.get("biggest_gac_commits", 0),
            "biggest_gac_commits_date": data.get("biggest_gac_commits_date"),
            "biggest_gac_files": data.get("biggest_gac_files", 0),
            "biggest_gac_files_date": data.get("biggest_gac_files_date"),
            "first_used": data.get("first_used"),
            "last_used": data.get("last_used"),
            "daily_gacs": data.get("daily_gacs", {}),
            "daily_commits": data.get("daily_commits", {}),
            "daily_prompt_tokens": data.get("daily_prompt_tokens", {}),
            "daily_output_tokens": data.get("daily_output_tokens", {}),
            "daily_reasoning_tokens": data.get("daily_reasoning_tokens", {}),
            "weekly_gacs": data.get("weekly_gacs", {}),
            "weekly_commits": data.get("weekly_commits", {}),
            "weekly_prompt_tokens": data.get("weekly_prompt_tokens", {}),
            "weekly_output_tokens": data.get("weekly_output_tokens", {}),
            "weekly_reasoning_tokens": data.get("weekly_reasoning_tokens", {}),
            "projects": data.get("projects", {}),
            "models": _normalize_models(data.get("models", {})),
            "history": data.get("history", []),
            "_version": data.get("_version", _CURRENT_STATS_VERSION),
        }
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load stats: {e}")
        return empty


def save_stats(stats: GACStats) -> None:
    """Save statistics to the stats file atomically.

    Writes to a temporary file in the same directory and then renames it
    over the destination so an interrupted write cannot leave a truncated
    or partially-written JSON file behind.

    Args:
        stats: GACStats dictionary to save
    """
    tmp_file = STATS_FILE.with_suffix(STATS_FILE.suffix + f".tmp.{os.getpid()}")
    try:
        STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp_file.write_text(json.dumps(stats, indent=2))
        os.replace(tmp_file, STATS_FILE)
    except OSError as e:
        logger.warning(f"Failed to save stats: {e}")
        try:
            tmp_file.unlink(missing_ok=True)
        except OSError:
            pass


def compute_total_tokens(data: dict[str, Any]) -> int:
    """Compute total tokens from a stats dict with prompt/output/reasoning keys.

    In v3 stats schema, output_tokens excludes reasoning_tokens (normalized
    at provider parse time), so total = prompt + output + reasoning (three
    distinct additive components).
    """
    return int(data.get("prompt_tokens", 0)) + int(data.get("output_tokens", 0)) + int(data.get("reasoning_tokens", 0))


def format_tokens(n: int) -> str:
    """Format a token count with thousands separators (e.g. 1,234,567)."""
    return f"{n:,}"


def project_activity(project_data: tuple[str, Any]) -> tuple[int, int]:
    """Sort key for projects by total activity (gacs + commits), then by total tokens.

    Args:
        project_data: Tuple of (project_name, data) where data is a dict
            with 'gacs', 'commits', 'prompt_tokens', 'output_tokens', and
            'reasoning_tokens' keys.

    Returns:
        Tuple of (activity, total_tokens) — higher sorts first when reverse=True.

    NOTE: In v3 stats schema, output_tokens excludes reasoning_tokens
    (normalized at provider parse time), so total = prompt + output +
    reasoning (three distinct additive components).
    """
    data = project_data[1]
    activity = int(data.get("gacs", 0)) + int(data.get("commits", 0))
    total_tokens = compute_total_tokens(data)
    return (activity, total_tokens)


def model_activity(model_data: tuple[str, Any]) -> tuple[int, int, int]:
    """Sort key for models by gacs, then commits, then by total tokens.

    Args:
        model_data: Tuple of (model_name, data) where data is a dict
            with 'gacs', 'commits', 'prompt_tokens', 'output_tokens', and
            'reasoning_tokens' keys.

    Returns:
        Tuple of (gacs, commits, total_tokens) — higher sorts first when reverse=True.

    NOTE: In v3 stats schema, output_tokens excludes reasoning_tokens
        (normalized at provider parse time), so total = prompt + output +
        reasoning (three distinct additive components).
    """
    data = model_data[1]
    gacs = int(data.get("gacs", 0))
    commits = int(data.get("commits", 0))
    total_tokens = compute_total_tokens(data)
    return (gacs, commits, total_tokens)


def reset_stats() -> None:
    """Reset all statistics to zero."""
    save_stats(_empty_stats())
    # Import here to avoid circular dependency at module level
    from gac.stats.recorder import _set_new_biggest_gac, reset_gac_token_accumulator

    reset_gac_token_accumulator()
    _set_new_biggest_gac(False)
    logger.info("Statistics reset")


def append_history(stats: GACStats, record: dict[str, Any]) -> None:
    """Append a per-gac history record and trim to HISTORY_CAP.

    The history is a ring buffer: newest records are at the end.
    When the cap is exceeded, the oldest records (front of the list)
    are dropped.

    Args:
        stats: The mutable stats dict to update.
        record: A dict with per-gac metadata (ts, project, model, tokens, etc).
    """
    history = stats.get("history", [])
    history.append(record)
    if len(history) > HISTORY_CAP:
        del history[: len(history) - HISTORY_CAP]
    stats["history"] = history


def find_model_key(models: dict[str, Any], model_id: str) -> str | None:
    """Find a model key in the models dict using case-insensitive matching.

    Args:
        models: Dict of model_name -> model_data
        model_id: The model identifier to find (e.g. 'wafer:deepseek-v4-pro')

    Returns:
        The original-cased key if found, None if not found.
    """
    model_id_lower = model_id.lower()
    for key in models:
        if key.lower() == model_id_lower:
            return key
    return None


def reset_model_stats(model_id: str) -> bool:
    """Reset statistics for a specific model (case-insensitive match).

    Args:
        model_id: The model identifier to reset (e.g. 'wafer:deepseek-v4-pro')

    Returns:
        True if the model was found and reset, False if not found.
    """
    if not stats_enabled():
        return False

    stats = load_stats()
    models = stats.get("models", {})

    matched_key = find_model_key(models, model_id)
    if matched_key is None:
        return False

    # Remove the model from stats (leave overall totals unchanged)
    del models[matched_key]
    save_stats(stats)
    logger.info(f"Reset statistics for model: {matched_key}")
    return True
