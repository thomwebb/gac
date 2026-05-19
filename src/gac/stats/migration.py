"""Schema migrations for gac usage statistics.

This module contains all version-to-version migration functions and the
file-location migration (``~/.gac_stats.json`` → ``~/.gac/stats.json``).
It also owns the constants that govern migration behaviour
(``_CURRENT_STATS_VERSION``, ``HISTORY_CAP``).
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CURRENT_STATS_VERSION = 5  # v5: biggest_gac_commits/files records

# Max history records (~150 bytes/record × 1000 = ~150 KB).
HISTORY_CAP = 1000


def _migrate_stats_file_location(
    stats_file: Path | None = None,
    legacy_file: Path | None = None,
) -> None:
    """One-time migration: move ~/.gac_stats.json → ~/.gac/stats.json.

    If the legacy file exists and the new doesn't, it is moved.
    If both exist, the legacy file is left alone.  Errors are logged
    but never raised — best-effort convenience migration.

    Args:
        stats_file: Path to the new stats file.  Defaults to
            ``gac.stats.store.STATS_FILE`` when not provided.
        legacy_file: Path to the legacy stats file.  Defaults to
            ``gac.stats.store._LEGACY_STATS_FILE`` when not provided.
    """
    # Resolve defaults lazily to avoid circular imports at module load.
    if stats_file is None or legacy_file is None:
        from gac.stats.store import _LEGACY_STATS_FILE, STATS_FILE

        stats_file = stats_file or STATS_FILE
        legacy_file = legacy_file or _LEGACY_STATS_FILE

    if not legacy_file.exists() or stats_file.exists():
        return
    try:
        stats_file.parent.mkdir(parents=True, exist_ok=True)
        legacy_file.rename(stats_file)
        logger.info(f"Migrated stats file: {legacy_file} → {stats_file}")
    except OSError as e:
        logger.warning(f"Could not migrate stats file location: {e}")


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


def _migrate_v3_to_v4(data: dict[str, Any]) -> dict[str, Any]:
    """Migrate stats from v3 to v4: add empty history ring buffer.

    v4 introduces a per-gac history ring buffer (capped at HISTORY_CAP)
    that stores individual gac metadata records. Existing aggregate
    fields are unchanged — they continue to be the primary data source
    for totals and breakdowns.
    """
    if int(data.get("_version", 0)) >= 4:
        return data

    data.setdefault("history", [])
    data["_version"] = 4
    return data


def _migrate_v4_to_v5(data: dict[str, Any]) -> dict[str, Any]:
    """Migrate stats from v4 to v5: add biggest_gac_commits and biggest_gac_files.

    v5 introduces two new "biggest gac" dimensions alongside the existing
    token-based one:
    - ``biggest_gac_commits`` / ``biggest_gac_commits_date``: the single gac
      invocation that produced the most commits (relevant for ``--group`` mode).
    - ``biggest_gac_files`` / ``biggest_gac_files_date``: the single gac
      invocation that touched the most files.

    For existing data, we backfill these from the history ring buffer
    when available; otherwise we default to 0 / None.
    """
    if int(data.get("_version", 0)) >= 5:
        return data

    # Backfill from history if available
    history = data.get("history", [])
    best_commits = 0
    best_commits_ts: str | None = None
    best_files = 0
    best_files_ts: str | None = None
    for record in history:
        commits = int(record.get("commits", 0))
        files = int(record.get("files", 0))
        if commits > best_commits:
            best_commits = commits
            best_commits_ts = record.get("ts")
        if files > best_files:
            best_files = files
            best_files_ts = record.get("ts")

    data.setdefault("biggest_gac_commits", best_commits)
    data.setdefault("biggest_gac_commits_date", best_commits_ts)
    data.setdefault("biggest_gac_files", best_files)
    data.setdefault("biggest_gac_files_date", best_files_ts)

    data["_version"] = 5
    return data


def _migrate(data: dict[str, Any]) -> dict[str, Any]:
    """Apply schema migrations in order until reaching the current version."""
    version = int(data.get("_version", 0))
    if version < 2:
        data = _migrate_v1_to_v2(data)
        version = int(data.get("_version", 0))
    if version < 3:
        data = _migrate_v2_to_v3(data)
        version = int(data.get("_version", 0))
    if version < 4:
        data = _migrate_v3_to_v4(data)
        version = int(data.get("_version", 0))
    if version < 5:
        data = _migrate_v4_to_v5(data)
    return data
