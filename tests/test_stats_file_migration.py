"""Tests for stats file location migration: ~/.gac_stats.json → ~/.gac/stats.json."""

from pathlib import Path
from unittest.mock import patch

from gac.stats.migration import _migrate_stats_file_location
from gac.stats.store import _LEGACY_STATS_FILE


class TestMigrateStatsFileLocation:
    """Tests for _migrate_stats_file_location()."""

    def test_no_legacy_file(self, tmp_path: Path) -> None:
        """If legacy file doesn't exist, migration is a no-op."""
        new_path = tmp_path / ".gac" / "stats.json"
        _migrate_stats_file_location(stats_file=new_path, legacy_file=tmp_path / "nope.json")
        # New path should NOT have been created
        assert not new_path.exists()

    def test_migrate_moves_file(self, tmp_path: Path) -> None:
        """If legacy exists and new doesn't, legacy is moved to new location."""
        legacy = tmp_path / "old_stats.json"
        legacy.write_text('{"total_gacs": 42, "_version": 4}')
        new_path = tmp_path / ".gac" / "stats.json"

        _migrate_stats_file_location(stats_file=new_path, legacy_file=legacy)

        # Legacy should be gone, new should exist with the same content
        assert not legacy.exists()
        assert new_path.exists()
        assert new_path.read_text() == '{"total_gacs": 42, "_version": 4}'

    def test_both_exist_skips_migration(self, tmp_path: Path) -> None:
        """If both files exist, migration is skipped (don't overwrite new data)."""
        legacy = tmp_path / "old_stats.json"
        legacy.write_text('{"total_gacs": 1}')
        new_path = tmp_path / ".gac" / "stats.json"
        new_path.parent.mkdir(parents=True, exist_ok=True)
        new_path.write_text('{"total_gacs": 99}')

        _migrate_stats_file_location(stats_file=new_path, legacy_file=legacy)

        # Both should still exist, new should be untouched
        assert legacy.exists()
        assert new_path.read_text() == '{"total_gacs": 99}'

    def test_migration_creates_parent_dir(self, tmp_path: Path) -> None:
        """Migration creates ~/.gac/ directory if it doesn't exist."""
        legacy = tmp_path / "old_stats.json"
        legacy.write_text('{"total_gacs": 5}')
        new_path = tmp_path / "nested" / "dir" / "stats.json"

        _migrate_stats_file_location(stats_file=new_path, legacy_file=legacy)

        assert not legacy.exists()
        assert new_path.exists()

    def test_migration_error_is_non_fatal(self, tmp_path: Path) -> None:
        """OSError during migration is logged but not raised."""
        legacy = tmp_path / "old_stats.json"
        legacy.write_text('{"total_gacs": 5}')

        # Point new_path at a path where the parent dir can't be created
        # by making a file where the directory would be
        blocker = tmp_path / "blocked"
        blocker.touch()
        new_path = blocker / "stats.json"  # blocker is a file, not a dir

        # Should not raise — OSError caught internally
        _migrate_stats_file_location(stats_file=new_path, legacy_file=legacy)

        # Legacy should still exist (rename didn't happen)
        assert legacy.exists()

    def test_load_stats_triggers_migration(self, tmp_path: Path) -> None:
        """load_stats() calls _migrate_stats_file_location() automatically."""
        legacy = tmp_path / "old_stats.json"
        legacy.write_text('{"total_gacs": 42, "_version": 4, "total_commits": 0}')
        new_path = tmp_path / ".gac" / "stats.json"

        with (
            patch("gac.stats.store._LEGACY_STATS_FILE", legacy),
            patch("gac.stats.store.STATS_FILE", new_path),
        ):
            from gac.stats.store import load_stats

            stats = load_stats()

        # File should have been moved, and data loaded from new location
        assert not legacy.exists()
        assert new_path.exists()
        assert stats["total_gacs"] == 42

    def test_legacy_path_constant(self) -> None:
        """_LEGACY_STATS_FILE points to the old location."""
        assert _LEGACY_STATS_FILE == Path.home() / ".gac_stats.json"

    def test_new_path_is_under_gac_dir(self) -> None:
        """STATS_FILE lives under ~/.gac/ (though conftest may redirect it)."""
        from gac.stats.store import STATS_FILE

        # The STATS_FILE should end with .gac/stats.json regardless of conftest override
        parts = STATS_FILE.parts
        assert ".gac" in parts
        assert STATS_FILE.name == "stats.json"
