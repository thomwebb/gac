#!/usr/bin/env python3
"""Preprocessing utilities for git diffs.

This module provides functions to preprocess git diffs for AI analysis,
with a focus on handling large repositories efficiently.
"""

import concurrent.futures
import logging
import os
import re

from gac.ai_utils import count_tokens
from gac.constants import (
    CodePatternImportance,
    FilePatterns,
    FileTypeImportance,
    Utility,
)

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
        elif "deleted file" in line:
            summary_lines.append(line)
        elif "new file" in line:
            summary_lines.append(line)
        elif line.startswith("index "):
            summary_lines.append(line)
        elif "Binary file" in line:
            summary_lines.append("[Binary file change]")
            break

    # If we didn't get a specific change type, determine it
    if not change_type and filename:
        if any(re.search(pattern, section) for pattern in FilePatterns.BINARY):
            change_type = "[Binary file change]"
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


def score_sections(sections: list[str]) -> list[tuple[str, float]]:
    """Score diff sections by importance.

    Args:
        sections: List of diff sections to score

    Returns:
        List of (section, score) tuples sorted by importance
    """
    scored_sections = []

    for section in sections:
        importance = calculate_section_importance(section)
        scored_sections.append((section, importance))

    return sorted(scored_sections, key=lambda x: x[1], reverse=True)


def calculate_section_importance(section: str) -> float:
    """Calculate importance score for a diff section.

    The algorithm considers:
    1. File extension and type
    2. The significance of the changes (structural, logic, etc.)
    3. The ratio of additions/deletions
    4. The presence of important code patterns

    Args:
        section: Diff section to score

    Returns:
        Float importance score (higher = more important)
    """
    importance = 1.0  # Base importance

    file_match = re.search(r"diff --git a/(.*?) b/", section)
    if not file_match:
        return importance

    filename = file_match.group(1)

    extension_score = get_extension_score(filename)
    importance *= extension_score

    if re.search(r"new file mode", section):
        importance *= 1.2
    elif re.search(r"deleted file mode", section):
        importance *= 1.1

    additions = len(re.findall(r"^\+[^+]", section, re.MULTILINE))
    deletions = len(re.findall(r"^-[^-]", section, re.MULTILINE))
    total_changes = additions + deletions

    if total_changes > 0:
        change_factor = 1.0 + min(1.0, 0.1 * (total_changes / 5))
        importance *= change_factor

    pattern_score = analyze_code_patterns(section)
    importance *= pattern_score

    return importance


def get_extension_score(filename: str) -> float:
    """Get importance score based on file extension.

    Args:
        filename: Filename to check

    Returns:
        Importance multiplier based on file extension
    """
    default_score = 1.0
    for pattern, score in FileTypeImportance.EXTENSIONS.items():
        if not pattern.startswith(".") and pattern in filename:
            return score

    _, ext = os.path.splitext(filename)
    if ext:
        return FileTypeImportance.EXTENSIONS.get(ext, default_score)

    return default_score


def analyze_code_patterns(section: str) -> float:
    """Analyze a diff section for important code patterns.

    Args:
        section: Diff section to analyze

    Returns:
        Pattern importance score multiplier
    """
    pattern_score = 1.0
    pattern_found = False

    for pattern, multiplier in CodePatternImportance.PATTERNS.items():
        if re.search(pattern, section, re.MULTILINE):
            pattern_score *= multiplier
            pattern_found = True

    if not pattern_found:
        pattern_score *= 0.9

    return pattern_score


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


def _truncate_section_to_budget(section: str, token_budget: int, model: str) -> str | None:
    """Truncate a single diff section to fit within *token_budget*.

    Always keeps the diff header and at least a portion of the first hunk.
    Returns ``None`` only for empty input. For extremely small budgets we still
    return a minimal, visible header snippet plus a truncation marker rather
    than an empty string.
    """
    trunc_marker = "\n... [Truncated due to token limits]"

    if not section:
        return None

    # Even with a zero/negative budget, prefer returning *something* visible
    # over silently dropping a section. The budget is a heuristic anyway.
    if token_budget <= 0:
        first_line = section.split("\n", 1)[0]
        return (first_line + trunc_marker) if first_line else trunc_marker.lstrip("\n")

    lines = section.split("\n")
    if not lines:
        return None

    header_lines: list[str] = []
    body_lines: list[str] = []
    in_body = False

    # Separate header from body (hunks).  The header is everything up to
    # and including the first ``@@`` hunk-header line.
    for line in lines:
        if not in_body:
            header_lines.append(line)
            if line.startswith("@@"):
                in_body = True
        else:
            body_lines.append(line)

    # Always start with the full header.
    header_text = "\n".join(header_lines)
    header_tokens = count_tokens(header_text, model)

    marker_tokens = count_tokens(trunc_marker, model)

    # If the budget can't even accommodate the full header plus marker, emit
    # a minimal header snippet + marker so the file is never silently dropped.
    if header_tokens + marker_tokens >= token_budget:
        remaining = max(1, token_budget - marker_tokens)
        result_lines: list[str] = []

        for line in header_lines:
            line_tokens = count_tokens(line + "\n", model)
            if line_tokens <= remaining:
                result_lines.append(line)
                remaining -= line_tokens
                continue

            # Include a truncated portion of this line.
            if line:
                chars_per_token = max(1.0, len(line) / max(line_tokens, 1))
                keep_chars = max(1, int(remaining * chars_per_token))
                result_lines.append(line[:keep_chars])
            break

        header_snippet = "\n".join(result_lines) if result_lines else section.split("\n", 1)[0]
        return header_snippet + trunc_marker

    # We have room for the header *and* some body.
    remaining = token_budget - header_tokens

    kept_body: list[str] = []
    for line in body_lines:
        line_tokens = count_tokens(line + "\n", model)
        if remaining < line_tokens + marker_tokens:
            # Room for the marker and maybe a bit of this line
            if remaining > marker_tokens:
                chars_per_token = max(1.0, len(line) / max(line_tokens, 1))
                keep_chars = int((remaining - marker_tokens) * chars_per_token)
                if keep_chars > 0:
                    kept_body.append(line[:keep_chars])
            break
        kept_body.append(line)
        remaining -= line_tokens

    result = header_text + "\n" + "\n".join(kept_body) + trunc_marker if kept_body else header_text + trunc_marker
    return result


def smart_truncate_diff(
    scored_sections: list[tuple[str, float]], token_limit: int, model: str, per_section_limit: int | None = None
) -> str:
    """Intelligently truncate a diff to fit within token limits.

    Key behaviour:
    - Fully-included sections are prioritised by importance score.
    - Sections that don't fit are **truncated** rather than silently dropped:
      at minimum the diff header plus the beginning of the first hunk is kept,
      with an explicit ``[Truncated due to token limits]`` marker.
    - Lockfile/generated-file stubs (compact summaries produced by
      ``process_section``) are always preserved in full — they are already
      minimal so truncating them would lose the only signal about the change.
    - A visibility summary at the end reports how many files were fully
      included, truncated, or summarised.

    Args:
        scored_sections: List of (section, score) tuples
        token_limit: Maximum tokens to include
        model: Model identifier for token counting

    Returns:
        Truncated diff
    """
    if not scored_sections:
        return ""

    result_sections: list[tuple[str, str]] = []
    current_tokens = 0
    included_count = 0
    truncated_count = 0
    summarized_count = 0
    total_count = len(scored_sections)

    # Detect stub/summary sections (from process_section filtering).
    _STUB_MARKERS = (
        "[Binary file change]",
        "[Lockfile/generated file change]",
        "[Minified file change]",
        "[Filtered file change]",
    )

    def _is_stub(section: str) -> bool:
        # Must contain a stub marker AND have no @@ hunk headers.
        # Real diffs always have @@ lines; stubs from extract_filtered_file_summary
        # are compact summaries without hunks.
        return any(marker in section for marker in _STUB_MARKERS) and "@@" not in section

    # De-duplicate by filename up-front (preserving the first occurrence as the "winner").
    # Then include all stub sections first so lockfile/generated/binary summaries are never
    # evicted by large code diffs.
    stub_sections: list[str] = []
    normal_sections: list[str] = []
    processed_files: set[str] = set()
    for section, _score in scored_sections:
        file_match = re.search(r"diff --git a/(.*?) b/", section)
        if not file_match:
            continue

        filename = file_match.group(1)
        if filename in processed_files:
            continue

        processed_files.add(filename)
        if _is_stub(section):
            stub_sections.append(section)
        else:
            normal_sections.append(section)

    def _append_full(section: str, *, stub: bool, filename: str) -> None:
        nonlocal current_tokens, included_count, summarized_count
        section_tokens = max(count_tokens(section, model), 1)
        result_sections.append((filename, section))
        current_tokens += section_tokens
        if stub:
            summarized_count += 1
        else:
            included_count += 1

    # First pass: stubs in full (these are intentionally compact summaries).
    for section in stub_sections:
        file_match = re.search(r"diff --git a/(.*?) b/", section)
        filename = file_match.group(1) if file_match else "(unknown)"
        _append_full(section, stub=True, filename=filename)

    # Second pass: include normal sections, truncating per-section or total as needed.
    for section in normal_sections:
        file_match = re.search(r"diff --git a/(.*?) b/", section)
        filename = file_match.group(1) if file_match else "(unknown)"
        section_tokens = max(count_tokens(section, model), 1)

        # Per-section limit: truncate if this individual section is too large.
        if per_section_limit is not None and section_tokens > per_section_limit:
            truncated = _truncate_section_to_budget(section, per_section_limit, model)
            if truncated:
                result_sections.append((filename, truncated))
                current_tokens += count_tokens(truncated, model)
                truncated_count += 1
            continue

        # Total budget limit.
        if current_tokens + section_tokens > token_limit:
            remaining_budget = token_limit - current_tokens
            truncated = _truncate_section_to_budget(section, remaining_budget, model)
            if truncated:
                result_sections.append((filename, truncated))
                current_tokens += count_tokens(truncated, model)
                truncated_count += 1
            continue

        _append_full(section, stub=False, filename=filename)

    # Build a visibility summary so the user knows what happened.
    summary_parts: list[str] = []
    if included_count > 0:
        summary_parts.append(f"{included_count} file(s) fully included")
    if truncated_count > 0:
        summary_parts.append(f"{truncated_count} file(s) truncated due to token limits")
    if summarized_count > 0:
        summary_parts.append(f"{summarized_count} file(s) summarized (lockfile/generated)")

    visibility_summary = ""
    if summary_parts and current_tokens + 100 <= token_limit:
        visibility_summary = (
            f"\n\n[Visibility summary: {', '.join(summary_parts)}."
            f" Total: {included_count + truncated_count + summarized_count} of {total_count} files"
            f" ({current_tokens}/{token_limit} tokens used).]"
        )

    # Build the final XML-wrapped output.
    xml_parts: list[str] = []
    for fname, content in result_sections:
        xml_parts.append(f'<file path="{fname}">\n{content}\n</file>')
    if visibility_summary:
        xml_parts.append(visibility_summary.lstrip("\n"))

    return "\n".join(xml_parts)
