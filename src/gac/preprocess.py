#!/usr/bin/env python3
"""Preprocessing utilities for git diffs.

This module provides functions to preprocess git diffs for AI analysis,
with a focus on handling large repositories efficiently.
"""

import concurrent.futures
import logging
import re

from gac.ai_utils import count_tokens
from gac.constants import FilePatterns, Utility
from gac.diff_scoring import score_sections, smart_truncate_diff

logger = logging.getLogger(__name__)

_LOCKFILE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"package-lock\.json$"),
    re.compile(r"yarn\.lock$"),
    re.compile(r"Pipfile\.lock$"),
    re.compile(r"poetry\.lock$"),
    re.compile(r"Gemfile\.lock$"),
    re.compile(r"pnpm-lock\.yaml$"),
    re.compile(r"composer\.lock$"),
    re.compile(r"Cargo\.lock$"),
    re.compile(r"uv\.lock$"),
    re.compile(r"\.sum$"),
]

_GENERATED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\.pb\.go$"),
    re.compile(r"\.g\.dart$"),
    re.compile(r"autogen\."),
    re.compile(r"generated\."),
]


def preprocess_diff(
    diff: str,
    token_limit: int = Utility.DEFAULT_DIFF_TOKEN_LIMIT,
    model: str = "anthropic:claude-3-haiku-latest",
    per_section_limit: int | None = Utility.PER_FILE_DIFF_TOKEN_LIMIT,
) -> str:
    """Preprocess a git diff to make it more suitable for AI analysis.

    This function processes a git diff by:
    1. Filtering out binary and minified files
    2. Scoring and prioritizing changes by importance
    3. Truncating to fit within token limits (total and per-section)
    4. Focusing on structural and important changes

    Args:
        diff: The git diff to process
        token_limit: Maximum tokens for the combined diff (default 192K).
        model: Model identifier for token counting
        per_section_limit: Maximum tokens per individual file section (default 16K).

    Returns:
        Processed diff optimized for AI consumption
    """
    if not diff:
        return diff

    initial_tokens = count_tokens(diff, model)
    if initial_tokens <= token_limit * 0.8:
        return filter_binary_and_minified(diff)

    logger.info(f"Processing large diff ({initial_tokens} tokens, limit {token_limit})")

    sections = split_diff_into_sections(diff)
    processed_sections = process_sections_parallel(sections)
    scored_sections = score_sections(processed_sections)
    truncated_diff = smart_truncate_diff(scored_sections, token_limit, model, per_section_limit=per_section_limit)

    return truncated_diff


def preprocess_per_file_diffs(
    per_file_diffs: list[tuple[str, str]],
    token_limit: int = Utility.DEFAULT_DIFF_TOKEN_LIMIT,
    model: str = "anthropic:claude-haiku-latest",
    per_section_limit: int | None = Utility.PER_FILE_DIFF_TOKEN_LIMIT,
) -> str:
    """Preprocess per-file diffs, bypassing regex-based section splitting.

    Each entry in *per_file_diffs* is a ``(filename, diff_content)`` tuple
    from ``get_staged_diffs_per_file()``.  Since each tuple already represents
    exactly one file, we can skip ``split_diff_into_sections`` and the
    attendant risk of false-positive splits on test-fixture ``diff --git``
    strings embedded in other files.

    Args:
        per_file_diffs: List of (filename, diff) tuples.
        token_limit: Maximum tokens for the combined diff (default 192K).
        model: Model identifier for token counting.
        per_section_limit: Maximum tokens per individual file (default 16K).
            Sections exceeding this are truncated before the total-budget
            check.  Pass ``None`` to disable per-section truncation.

    Returns:
        Processed diff string ready for inclusion in the AI prompt.
    """
    if not per_file_diffs:
        return ""

    logger.info(
        f"Processing {len(per_file_diffs)} per-file diffs"
        f" (total limit {token_limit}, per-section limit {per_section_limit})"
    )

    # Each per-file diff is already one section — process individually.
    processed_sections: list[str] = []
    for _filename, diff_content in per_file_diffs:
        result = process_section(diff_content)
        if result:
            processed_sections.append(result)

    scored_sections = score_sections(processed_sections)
    return smart_truncate_diff(scored_sections, token_limit, model, per_section_limit=per_section_limit)


def split_diff_into_sections(diff: str) -> list[str]:
    """Split a git diff into individual file sections.

    Args:
        diff: Full git diff

    Returns:
        List of individual file sections
    """
    if not diff:
        return []

    return [s for s in re.split(r"(?=diff --git )", diff) if s]


def process_sections_parallel(sections: list[str]) -> list[str]:
    """Process diff sections in parallel for better performance.

    Args:
        sections: List of diff sections to process

    Returns:
        List of processed sections (filtered)
    """
    # Small number of sections - process sequentially to avoid overhead
    if len(sections) <= 3:
        processed = []
        for section in sections:
            result = process_section(section)
            if result:
                processed.append(result)
        return processed

    filtered_sections = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=Utility.MAX_WORKERS) as executor:
        future_to_section = {executor.submit(process_section, section): section for section in sections}
        for future in concurrent.futures.as_completed(future_to_section):
            result = future.result()
            if result:
                filtered_sections.append(result)

    return filtered_sections


def process_section(section: str) -> str | None:
    """Process a single diff section.

    Args:
        section: Diff section to process

    Returns:
        Processed section or None if it should be filtered
    """
    if should_filter_section(section):
        # Return a summary for filtered files instead of removing completely
        return extract_filtered_file_summary(section)
    return section


def extract_binary_file_summary(section: str) -> str:
    """Extract a summary of binary file changes from a diff section.

    Args:
        section: Binary file diff section

    Returns:
        Summary string showing the binary file change
    """
    return extract_filtered_file_summary(section, "[Binary file change]")


def extract_filtered_file_summary(section: str, change_type: str | None = None) -> str:
    """Extract a summary of filtered file changes from a diff section.

    Args:
        section: Diff section for a filtered file
        change_type: Optional custom change type message

    Returns:
        Summary string showing the file change
    """
    lines = section.strip().split("\n")
    summary_lines = []
    filename = None

    # Keep the diff header and important metadata
    for line in lines:
        if line.startswith("diff --git"):
            summary_lines.append(line)
            # Extract filename
            match = re.search(r"diff --git a/(.*?) b/", line)
            if match:
                filename = match.group(1)
        elif line.startswith("deleted file"):
            summary_lines.append(line)
        elif line.startswith("new file"):
            summary_lines.append(line)
        elif line.startswith("index "):
            summary_lines.append(line)
        elif line.startswith("Binary file"):
            summary_lines.append("[Binary file change]")
            break

    # If we didn't get a specific change type, determine it
    if not change_type and filename:
        if any(re.search(pattern, section) for pattern in FilePatterns.BINARY):
            change_type = "[Binary file change]"
        elif is_deleted_file_section(section):
            change_type = "[Deleted file]"
        elif is_lockfile_or_generated(filename):
            change_type = "[Lockfile/generated file change]"
        elif any(filename.endswith(ext) for ext in FilePatterns.MINIFIED_EXTENSIONS):
            change_type = "[Minified file change]"
        elif is_minified_content(section):
            change_type = "[Minified file change]"
        else:
            change_type = "[Filtered file change]"

    if change_type and change_type not in "\n".join(summary_lines):
        summary_lines.append(change_type)

    return "\n".join(summary_lines) + "\n" if summary_lines else ""


def should_filter_section(section: str) -> bool:
    """Determine if a section should be filtered out.

    Args:
        section: Diff section to check

    Returns:
        True if the section should be filtered out, False otherwise
    """
    if any(re.search(pattern, section) for pattern in FilePatterns.BINARY):
        file_match = re.search(r"diff --git a/(.*?) b/", section)
        if file_match:
            filename = file_match.group(1)
            logger.info(f"Filtered out binary file: {filename}")
        return True
    file_match = re.search(r"diff --git a/(.*?) b/", section)
    if file_match:
        filename = file_match.group(1)

        if is_deleted_file_section(section):
            logger.info(f"Summarized deleted file: {filename}")
            return True

        if any(filename.endswith(ext) for ext in FilePatterns.MINIFIED_EXTENSIONS):
            logger.info(f"Filtered out minified file by extension: {filename}")
            return True

        if any(directory in filename for directory in FilePatterns.BUILD_DIRECTORIES):
            logger.info(f"Filtered out file in build directory: {filename}")
            return True

        if is_lockfile_or_generated(filename):
            logger.info(f"Filtered out lockfile or generated file: {filename}")
            return True

        if is_minified_content(section):
            logger.info(f"Filtered out likely minified file by content: {filename}")
            return True

    return False


def is_deleted_file_section(section: str) -> bool:
    """Check if a diff section represents a deleted file.

    A pure deletion includes the entire previous file content as ``-`` lines,
    which can bloat the AI context for no benefit — the filename plus the
    fact of deletion is enough to write a useful commit message.

    Args:
        section: Diff section to check

    Returns:
        True if the section's header marks the file as deleted
    """
    return bool(re.search(r"^deleted file mode", section, re.MULTILINE))


def is_lockfile_or_generated(filename: str) -> bool:
    """Check if a file appears to be a lockfile or generated.

    Args:
        filename: Name of the file to check

    Returns:
        True if the file is likely a lockfile or generated
    """
    return any(p.search(filename) for p in _LOCKFILE_PATTERNS) or any(p.search(filename) for p in _GENERATED_PATTERNS)


def is_minified_content(content: str) -> bool:
    """Check if file content appears to be minified based on heuristics.

    Args:
        content: File content to check

    Returns:
        True if the content appears to be minified
    """
    if not content:
        return False

    lines = content.split("\n")
    if not lines:
        return False

    if len(lines) < 10 and len(content) > 1000:
        return True

    if len(lines) == 1 and len(lines[0]) > 200:
        return True

    if any(len(line.strip()) > 300 and line.count(" ") < len(line) / 20 for line in lines):
        return True

    long_lines_count = sum(1 for line in lines if len(line) > 500)

    if long_lines_count > 0 and (long_lines_count / len(lines)) > 0.2:
        return True

    return False


def filter_binary_and_minified(diff: str) -> str:
    """Filter out binary and minified files from a git diff.

    This is a simplified version that processes the diff as a whole, used for
    smaller diffs that don't need full optimization.

    Args:
        diff: Git diff to process

    Returns:
        Filtered diff
    """
    if not diff:
        return diff

    sections = split_diff_into_sections(diff)
    filtered_sections = []
    for section in sections:
        if should_filter_section(section):
            # Extract summaries for filtered files instead of removing completely
            filtered_section = extract_filtered_file_summary(section)
            if filtered_section:
                filtered_sections.append(filtered_section)
        else:
            filtered_sections.append(section)

    return "\n".join(filtered_sections)
