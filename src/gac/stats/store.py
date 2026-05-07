"""Stats persistence layer — loading, saving, and migrating usage data."""

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

logger = logging.getLogger(__name__)

STATS_FILE = Path.home() / ".gac_stats.json"

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


# =============================================================================
# TYPED DICT
# =============================================================================


class GACStats(TypedDict):
    """TypedDict for GAC usage statistics."""

    total_gacs: int  # Number of gac workflow runs
    total_commits: int  # Number of actual commits created
    total_prompt_tokens: int  # Total prompt tokens consumed
    total_output_tokens: int  # Total output tokens consumed (excludes reasoning)
    total_reasoning_tokens: int  # Total reasoning/thinking tokens consumed
    biggest_gac_tokens: int  # Most tokens (prompt+output+reasoning) in a single gac run
    biggest_gac_date: str | None  # ISO datetime when the biggest gac occurred
    first_used: str | None
    last_used: str | None
    daily_gacs: dict[str, int]  # date -> gac count
    daily_commits: dict[str, int]  # date -> commit count
    daily_prompt_tokens: dict[str, int]  # date -> prompt token count
    daily_output_tokens: dict[str, int]  # date -> output token count (excludes reasoning)
    daily_reasoning_tokens: dict[str, int]  # date -> reasoning token count
    weekly_gacs: dict[str, int]  # ISO week (e.g. 2026-W18) -> gac count
    weekly_commits: dict[str, int]  # ISO week -> commit count
    weekly_prompt_tokens: dict[str, int]  # ISO week -> prompt token count
    weekly_output_tokens: dict[str, int]  # ISO week -> output token count (excludes reasoning)
    weekly_reasoning_tokens: dict[str, int]  # ISO week -> reasoning token count
    projects: dict[str, Any]  # project_name -> {gacs, commits, prompt_tokens, output_tokens, reasoning_tokens}
    models: dict[str, Any]  # model_name -> {gacs, prompt_tokens, output_tokens, reasoning_tokens}
    _version: int  # Schema version for migrations


_CURRENT_STATS_VERSION = 3  # v3: output_tokens excludes reasoning_tokens; rename completion→output


# =============================================================================
# HELPERS
# =============================================================================


def _normalize_models(models: dict[str, Any]) -> dict[str, Any]:
    for _name, data in models.items():
        for field, default in _DURATION_DEFAULTS.items():
            data.setdefault(field, default)
    return models


def _enrich_models_with_speed(models: list[tuple[str, Any]]) -> list[tuple[str, Any]]:
    enriched: list[tuple[str, Any]] = []
    for name, data in models:
        avg_tps = None
        avg_latency_ms = None
        if data.get("duration_count", 0) > 0 and data.get("total_duration_ms", 0) > 0:
            # Speed = all output tokens (output text + reasoning) per second.
            # Reasoning tokens are generated during the same wall-clock
            # duration, so excluding them understates throughput for
            # thinking models like o3, deepseek-r1, etc.
            timed_output = data["timed_output_tokens"] + data.get("timed_reasoning_tokens", 0)
            avg_tps = round(timed_output * 1000 / data["total_duration_ms"])
            # Average latency = mean wall-clock time per API call (ms)
            avg_latency_ms = round(data["total_duration_ms"] / data["duration_count"])
        enriched.append((name, {**data, "avg_tps": avg_tps, "avg_latency_ms": avg_latency_ms}))
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


# =============================================================================
# MIGRATION
# =============================================================================


def _migrate_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
    """Migrate stats from v1 (inclusive completion) to v2 (exclusive).

    In v1, provider APIs returned ``completion_tokens`` inclusive of
    ``reasoning_tokens``, and we stored both verbatim.  In v2, we
    normalize at parse time so ``completion_tokens`` excludes reasoning.
    This migration subtracts stored ``reasoning_tokens`` from every
    completion field so old data matches the new contract.

    Fields migrated:
    - models: completion_tokens -= reasoning_tokens
    - projects: completion_tokens -= reasoning_tokens (if present)
    - daily/weekly: completion_tokens[key] -= reasoning_tokens[key]
    - total_completion_tokens -= total_reasoning_tokens
    - biggest_gac_tokens: reset to 0 since per-gac reasoning breakdown
      is not stored; the correct value will be set on the next gac that
      exceeds all prior *correct* per-gac totals
    """
    # Skip if already migrated
    if data.get("_version", 0) >= 2:
        return data

    # 1. Migrate models
    for _name, m in data.get("models", {}).items():
        rt = int(m.get("reasoning_tokens", 0))
        if rt > 0:
            m["completion_tokens"] = max(int(m.get("completion_tokens", 0)) - rt, 0)
            # Proportionally adjust timed_completion_tokens and derive
            # timed_reasoning_tokens so that speed (which sums both)
            # stays consistent across the migration boundary.
            tc = int(m.get("timed_completion_tokens", 0))
            if tc > 0:
                old_total = int(m.get("completion_tokens", 0)) + rt  # original inclusive
                if old_total > 0:
                    ratio = int(m["completion_tokens"]) / old_total
                    new_timed_comp = max(round(tc * ratio), 0)
                    m["timed_reasoning_tokens"] = max(tc - new_timed_comp, 0)
                    m["timed_completion_tokens"] = new_timed_comp

    # 2. Migrate projects
    for _name, p in data.get("projects", {}).items():
        rt = int(p.get("reasoning_tokens", 0))
        if rt > 0:
            p["completion_tokens"] = max(int(p.get("completion_tokens", 0)) - rt, 0)

    # 3. Migrate daily
    daily_comp = data.get("daily_completion_tokens", {})
    daily_reason = data.get("daily_reasoning_tokens", {})
    for key in daily_comp:
        rt = int(daily_reason.get(key, 0))
        if rt > 0:
            daily_comp[key] = max(int(daily_comp[key]) - rt, 0)

    # 4. Migrate weekly
    weekly_comp = data.get("weekly_completion_tokens", {})
    weekly_reason = data.get("weekly_reasoning_tokens", {})
    for key in weekly_comp:
        rt = int(weekly_reason.get(key, 0))
        if rt > 0:
            weekly_comp[key] = max(int(weekly_comp[key]) - rt, 0)

    # 5. Migrate total_completion_tokens
    total_rt = int(data.get("total_reasoning_tokens", 0))
    if total_rt > 0:
        data["total_completion_tokens"] = max(int(data.get("total_completion_tokens", 0)) - total_rt, 0)

    # 6. Reset biggest_gac_tokens when reasoning existed
    has_reasoning = total_rt > 0 or any(int(m.get("reasoning_tokens", 0)) > 0 for m in data.get("models", {}).values())
    if has_reasoning:
        data["biggest_gac_tokens"] = 0
        data["biggest_gac_date"] = None

    data["_version"] = 2
    return data


def _migrate_v2_to_v3(data: dict[str, Any]) -> dict[str, Any]:
    """Migrate stats from v2 (completion_tokens) to v3 (output_tokens).

    v2 already stores completion/output tokens *exclusive* of reasoning
    (normalized at provider parse time).  v3 keeps the same numeric
    contract, but renames the fields to reduce ambiguity around the word
    "completion" for thinking models.

    Renames:
    - total_completion_tokens -> total_output_tokens
    - daily_completion_tokens -> daily_output_tokens
    - weekly_completion_tokens -> weekly_output_tokens
    - models[*].completion_tokens -> output_tokens
    - models[*].timed_completion_tokens -> timed_output_tokens
    - projects[*].completion_tokens -> output_tokens
    """
    if int(data.get("_version", 0)) >= 3:
        return data

    def _rename_top_level_int(old: str, new: str) -> None:
        if new not in data and old in data:
            data[new] = int(data.get(old, 0))
            del data[old]
        elif old in data:
            # Prefer the new key when both exist (avoid accidental double-count).
            del data[old]

    def _rename_top_level_dict(old: str, new: str) -> None:
        if new not in data and old in data and isinstance(data[old], dict):
            data[new] = data[old]
            del data[old]
        elif old in data:
            del data[old]

    _rename_top_level_int("total_completion_tokens", "total_output_tokens")
    _rename_top_level_dict("daily_completion_tokens", "daily_output_tokens")
    _rename_top_level_dict("weekly_completion_tokens", "weekly_output_tokens")

    # models: completion_tokens -> output_tokens; timed_completion_tokens -> timed_output_tokens
    models = data.get("models", {})
    if isinstance(models, dict):
        for _name, m in models.items():
            if not isinstance(m, dict):
                continue
            if "output_tokens" not in m and "completion_tokens" in m:
                m["output_tokens"] = m["completion_tokens"]
            m.pop("completion_tokens", None)
            if "timed_output_tokens" not in m and "timed_completion_tokens" in m:
                m["timed_output_tokens"] = m["timed_completion_tokens"]
            m.pop("timed_completion_tokens", None)

    # projects: completion_tokens -> output_tokens
    projects = data.get("projects", {})
    if isinstance(projects, dict):
        for _name, p in projects.items():
            if not isinstance(p, dict):
                continue
            if "output_tokens" not in p and "completion_tokens" in p:
                p["output_tokens"] = p["completion_tokens"]
            p.pop("completion_tokens", None)

    data["_version"] = 3
    return data


def _migrate(data: dict[str, Any]) -> dict[str, Any]:
    """Apply schema migrations in order until reaching the current version."""
    version = int(data.get("_version", 0))
    if version < 2:
        data = _migrate_v1_to_v2(data)
        version = int(data.get("_version", 0))
    if version < 3:
        data = _migrate_v2_to_v3(data)
    return data


# =============================================================================
# LOAD / SAVE / RESET
# =============================================================================


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
        "_version": _CURRENT_STATS_VERSION,
    }


def load_stats() -> GACStats:
    """Load statistics from the stats file.

    Returns:
        GACStats dictionary with usage statistics
    """
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


def model_activity(model_data: tuple[str, Any]) -> tuple[int, int]:
    """Sort key for models by gacs (workflow uses), then by total tokens.

    Args:
        model_data: Tuple of (model_name, data) where data is a dict
            with 'gacs', 'prompt_tokens', 'output_tokens', and 'reasoning_tokens' keys.

    Returns:
        Tuple of (gacs, total_tokens) — higher sorts first when reverse=True.

    NOTE: In v3 stats schema, output_tokens excludes reasoning_tokens
    (normalized at provider parse time), so total = prompt + output +
    reasoning (three distinct additive components).
    """
    data = model_data[1]
    gacs = int(data.get("gacs", 0))
    total_tokens = compute_total_tokens(data)
    return (gacs, total_tokens)


def reset_stats() -> None:
    """Reset all statistics to zero."""
    save_stats(_empty_stats())
    # Import here to avoid circular dependency at module level
    from gac.stats.recorder import _set_new_biggest_gac, reset_gac_token_accumulator

    reset_gac_token_accumulator()
    _set_new_biggest_gac(False)
    logger.info("Statistics reset")


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
