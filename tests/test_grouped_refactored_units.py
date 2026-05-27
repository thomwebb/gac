"""Tests for grouped response parsing, validation, and retry behavior.

These tests verify the refactored boundaries:

1. ``parse_json_response`` – structural validation of AI JSON output
2. ``validate_file_coverage`` – file-coverage checking
3. ``should_exit_or_retry`` – retry/feedback loop decisions
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from gac.grouped_response_parser import _strip_code_fences, parse_json_response, validate_file_coverage
from gac.grouped_retry_loop import should_exit_or_retry

# ── _strip_code_fences ──────────────────────────────────────────────────


class TestStripCodeFences:
    """Unit tests for _strip_code_fences helper."""

    def test_single_json_fence(self):
        """Single ```json fence is stripped, contents returned."""
        text = '```json\n{"key": true}\n```'
        assert _strip_code_fences(text) == '{"key": true}'

    def test_single_json_fence_no_newlines(self):
        """Single ```json{...}`` without newlines is stripped."""
        text = '```json{"key": true}```'
        assert _strip_code_fences(text) == '{"key": true}'

    def test_single_plain_fence(self):
        """Single ``` fence (no lang) is stripped."""
        text = '```\n{"key": true}\n```'
        assert _strip_code_fences(text) == '{"key": true}'

    def test_fence_with_whitespace(self):
        """Whitespace around fence content is stripped."""
        text = '```json\n  {"key": true}  \n```'
        assert _strip_code_fences(text) == '{"key": true}'

    def test_multiple_fences_returns_original(self):
        """Multiple fences → return original (let brace fallback handle it)."""
        text = '```json\n{"a": 1}\n```\n```\n{"b": 2}\n```'
        assert _strip_code_fences(text) == text

    def test_no_fence_returns_original(self):
        """No fences at all → return original."""
        text = '{"key": true}'
        assert _strip_code_fences(text) == text


# ── parse_json_response ────────────────────────────────────────────────────


class TestParseJsonResponse:
    """Unit tests for parse_json_response."""

    def test_valid_response(self):
        """A well-formed JSON response is parsed and returned."""
        raw = '{"commits": [{"files": ["a.py"], "message": "fix: bug"}]}'
        result = parse_json_response(raw)
        assert len(result["commits"]) == 1
        assert result["commits"][0]["files"] == ["a.py"]

    def test_json_embedded_in_markdown(self):
        """JSON wrapped in ```json fences is extracted correctly."""
        raw = '```json\n{"commits": [{"files": ["a.py"], "message": "fix: bug"}]}\n```'
        result = parse_json_response(raw)
        assert len(result["commits"]) == 1

    def test_json_in_plain_code_fence(self):
        """JSON wrapped in ``` (no language tag) fences is extracted."""
        raw = '```\n{"commits": [{"files": ["a.py"], "message": "fix: bug"}]}\n```'
        result = parse_json_response(raw)
        assert len(result["commits"]) == 1

    def test_code_fence_with_trailing_braces(self):
        """Fence stripping prevents trailing } outside the fence from breaking parsing."""
        raw = '```json\n{"commits": [{"files": ["a.py"], "message": "fix"}]}\n```\n\nSee format: {}'
        result = parse_json_response(raw)
        assert len(result["commits"]) == 1

    def test_code_fence_with_preamble_text(self):
        """Fence stripping ignores preamble text with braces."""
        raw = 'Here is your output {}\n\n```json\n{"commits": [{"files": ["a.py"], "message": "fix"}]}\n```'
        result = parse_json_response(raw)
        assert len(result["commits"]) == 1

    def test_multiple_code_fences_falls_back_to_braces(self):
        """When multiple fences exist, brace-based fallback kicks in."""
        raw = '```json\n{"commits": [{"files": ["a.py"], "message": "fix"}]}\n```\n```\nsome other block\n```'
        # Multiple fences → _strip_code_fences returns original → brace fallback
        result = parse_json_response(raw)
        assert len(result["commits"]) == 1

    def test_no_code_fence_uses_brace_fallback(self):
        """Plain JSON without fences works via brace-based extraction."""
        raw = 'Here is the response: {"commits": [{"files": ["a.py"], "message": "fix"}]}'
        result = parse_json_response(raw)
        assert len(result["commits"]) == 1

    def test_code_fence_json_no_language_tag(self):
        """Fence with no language tag still strips correctly."""
        raw = '```\n{"commits": [{"files": ["b.py"], "message": "feat: add"}]}\n```'
        result = parse_json_response(raw)
        assert len(result["commits"]) == 1
        assert result["commits"][0]["files"] == ["b.py"]

    def test_json_fenced_no_newlines(self):
        """```json{...}``` without newlines is parsed correctly."""
        raw = '```json{"commits": [{"files": ["a.py"], "message": "fix: bug"}]}```'
        result = parse_json_response(raw)
        assert len(result["commits"]) == 1

    def test_plain_fence_no_newlines(self):
        """```{...}``` without newlines is parsed correctly."""
        raw = '```{"commits": [{"files": ["a.py"], "message": "fix"}]}```'
        result = parse_json_response(raw)
        assert len(result["commits"]) == 1

    def test_invalid_json_raises_value_error(self):
        """Non-JSON input raises ValueError."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_json_response("this is not json at all")

    def test_missing_commits_key_raises_value_error(self):
        """Response without 'commits' key raises ValueError."""
        with pytest.raises(ValueError, match="missing 'commits' array"):
            parse_json_response('{"data": []}')

    def test_commits_not_list_raises_value_error(self):
        """'commits' that isn't a list raises ValueError."""
        with pytest.raises(ValueError, match="missing 'commits' array"):
            parse_json_response('{"commits": "not a list"}')

    def test_empty_commits_raises_value_error(self):
        """Empty commits array raises ValueError."""
        with pytest.raises(ValueError, match="No commits"):
            parse_json_response('{"commits": []}')

    def test_commit_missing_files_raises_value_error(self):
        """Commit without 'files' key raises ValueError."""
        with pytest.raises(ValueError, match="missing 'files' array"):
            parse_json_response('{"commits": [{"message": "fix"}]}')

    def test_commit_missing_message_raises_value_error(self):
        """Commit without 'message' key raises ValueError."""
        with pytest.raises(ValueError, match="missing 'message' string"):
            parse_json_response('{"commits": [{"files": ["a.py"]}]}')

    def test_commit_empty_files_raises_value_error(self):
        """Commit with empty files list raises ValueError."""
        with pytest.raises(ValueError, match="empty files list"):
            parse_json_response('{"commits": [{"files": [], "message": "fix"}]}')

    def test_commit_empty_message_raises_value_error(self):
        """Commit with whitespace-only message raises ValueError."""
        with pytest.raises(ValueError, match="empty message"):
            parse_json_response('{"commits": [{"files": ["a.py"], "message": "   "}]}')

    def test_multiple_commits_valid(self):
        """Multiple valid commits are accepted."""
        raw = '{"commits": [{"files": ["a.py"], "message": "fix: a"}, {"files": ["b.py"], "message": "feat: b"}]}'
        result = parse_json_response(raw)
        assert len(result["commits"]) == 2

    def test_files_as_non_list_raises_value_error(self):
        """'files' that isn't a list raises ValueError."""
        with pytest.raises(ValueError, match="missing 'files' array"):
            parse_json_response('{"commits": [{"files": "a.py", "message": "fix"}]}')

    def test_message_as_non_string_raises_value_error(self):
        """'message' that isn't a string raises ValueError."""
        with pytest.raises(ValueError, match="missing 'message' string"):
            parse_json_response('{"commits": [{"files": ["a.py"], "message": 42}]}')


# ── validate_file_coverage ────────────────────────────────────────────────


class TestValidateFileCoverage:
    """Unit tests for validate_file_coverage."""

    def test_exact_match_returns_valid(self):
        """When files exactly match staged set, validation passes."""
        staged = {"a.py", "b.py"}
        result = {"commits": [{"files": ["a.py"], "message": "fix"}, {"files": ["b.py"], "message": "feat"}]}
        ok, feedback, detail = validate_file_coverage(staged, result)
        assert ok is True
        assert feedback == ""
        assert detail == ""

    def test_missing_files_returns_invalid(self):
        """When staged files are missing from commits, validation fails."""
        staged = {"a.py", "b.py", "c.py"}
        result = {"commits": [{"files": ["a.py"], "message": "fix"}]}
        ok, feedback, detail = validate_file_coverage(staged, result)
        assert ok is False
        assert "Missing" in feedback
        assert "c.py" in feedback

    def test_unexpected_files_returns_invalid(self):
        """When commits reference non-staged files, validation fails."""
        staged = {"a.py"}
        result = {"commits": [{"files": ["a.py", "extra.py"], "message": "fix"}]}
        ok, feedback, detail = validate_file_coverage(staged, result)
        assert ok is False
        assert "Not staged" in feedback
        assert "extra.py" in feedback

    def test_duplicate_files_returns_invalid(self):
        """When a file appears in multiple commits, validation fails."""
        staged = {"a.py", "b.py"}
        result = {"commits": [{"files": ["a.py"], "message": "fix"}, {"files": ["a.py", "b.py"], "message": "feat"}]}
        ok, feedback, detail = validate_file_coverage(staged, result)
        assert ok is False
        assert "Duplicates" in feedback
        assert "a.py" in feedback

    def test_non_dict_input_returns_valid(self):
        """Non-dict input passes (let structural validation handle it)."""
        ok, feedback, detail = validate_file_coverage({"a.py"}, "not a dict")
        assert ok is True

    def test_empty_commits_returns_valid(self):
        """Empty commits list passes (defensive — caught elsewhere)."""
        ok, feedback, detail = validate_file_coverage({"a.py"}, {"commits": []})
        assert ok is True

    def test_commit_without_files_key_returns_valid(self):
        """Commit missing 'files' key passes (let structural validation handle)."""
        ok, feedback, detail = validate_file_coverage({"a.py"}, {"commits": [{"message": "fix"}]})
        assert ok is True

    def test_feedback_includes_required_files(self):
        """Feedback message includes the required file list."""
        staged = {"z.py"}
        result = {"commits": [{"files": ["other.py"], "message": "fix"}]}
        ok, feedback, detail = validate_file_coverage(staged, result)
        assert "z.py" in feedback


# ── should_exit_or_retry ──────────────────────────────────────────────────


class TestShouldExitOrRetry:
    """Unit tests for should_exit_or_retry."""

    def test_within_budget_returns_false(self):
        """When attempts < budget, should retry (returns False)."""
        messages: list[dict[str, str]] = []
        exit_ = should_exit_or_retry(
            attempts=1,
            budget=3,
            raw_response="bad output",
            feedback_message="fix it",
            error_message="exhausted",
            conversation_messages=messages,
            quiet=True,
            retry_context="testing",
        )
        assert exit_ is False
        # Messages were appended
        assert len(messages) == 2
        assert messages[0]["role"] == "assistant"
        assert messages[1]["role"] == "user"

    def test_at_budget_returns_true(self):
        """When attempts >= budget, should exit (returns True)."""
        messages: list[dict[str, str]] = []
        with patch("gac.grouped_retry_loop.console"):
            exit_ = should_exit_or_retry(
                attempts=3,
                budget=3,
                raw_response="bad output",
                feedback_message="fix it",
                error_message="exhausted",
                conversation_messages=messages,
                quiet=True,
                retry_context="testing",
            )
        assert exit_ is True

    def test_messages_appended_before_decision(self):
        """Assistant + user messages are appended regardless of exit decision."""
        messages: list[dict[str, str]] = []
        with patch("gac.grouped_retry_loop.console"):
            should_exit_or_retry(
                attempts=3,
                budget=3,
                raw_response="bad",
                feedback_message="fix",
                error_message="done",
                conversation_messages=messages,
                quiet=True,
                retry_context="testing",
            )
        assert len(messages) == 2

    def test_quiet_suppresses_output(self):
        """With quiet=True, no console output is produced during retry."""
        messages: list[dict[str, str]] = []
        with patch("gac.grouped_retry_loop.console") as mock_console:
            should_exit_or_retry(
                attempts=1,
                budget=3,
                raw_response="bad",
                feedback_message="fix",
                error_message="done",
                conversation_messages=messages,
                quiet=True,
                retry_context="testing",
            )
        mock_console.print.assert_not_called()

    def test_not_quiet_shows_retry_info(self):
        """With quiet=False, retry progress is shown."""
        messages: list[dict[str, str]] = []
        with patch("gac.grouped_retry_loop.console") as mock_console:
            should_exit_or_retry(
                attempts=1,
                budget=3,
                raw_response="bad",
                feedback_message="fix",
                error_message="done",
                conversation_messages=messages,
                quiet=False,
                retry_context="Structure validation failed",
            )
        # Should have printed retry info
        assert mock_console.print.called
