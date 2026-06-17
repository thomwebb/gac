#!/usr/bin/env python3
"""Tests for binary file detection module."""

import pytest

from gac.binary import (
    BinaryPatterns,
    detect_binary_files,
    format_file_size,
    identify_from_magic_bytes,
    is_binary_file,
)


class TestBinaryPatterns:
    """Test BinaryPatterns class."""

    def test_executable_extensions(self):
        """Test that common executable extensions are recognized."""
        assert ".exe" in BinaryPatterns.EXECUTABLE_EXTENSIONS
        assert ".dll" in BinaryPatterns.EXECUTABLE_EXTENSIONS
        assert ".so" in BinaryPatterns.EXECUTABLE_EXTENSIONS
        assert ".dylib" in BinaryPatterns.EXECUTABLE_EXTENSIONS

    def test_image_extensions(self):
        """Test that common image extensions are recognized."""
        assert ".png" in BinaryPatterns.IMAGE_EXTENSIONS
        assert ".jpg" in BinaryPatterns.IMAGE_EXTENSIONS
        assert ".jpeg" in BinaryPatterns.IMAGE_EXTENSIONS
        assert ".gif" in BinaryPatterns.IMAGE_EXTENSIONS

    def test_all_binary_extensions_union(self):
        """Test that ALL_BINARY_EXTENSIONS is a union of all categories."""
        assert BinaryPatterns.EXECUTABLE_EXTENSIONS.issubset(BinaryPatterns.ALL_BINARY_EXTENSIONS)
        assert BinaryPatterns.IMAGE_EXTENSIONS.issubset(BinaryPatterns.ALL_BINARY_EXTENSIONS)
        assert BinaryPatterns.MEDIA_EXTENSIONS.issubset(BinaryPatterns.ALL_BINARY_EXTENSIONS)

    def test_get_description_for_extension(self):
        """Test getting descriptions for known extensions."""
        assert "executable" in BinaryPatterns.get_description_for_extension(".exe").lower()
        assert "image" in BinaryPatterns.get_description_for_extension(".png").lower()
        assert "archive" in BinaryPatterns.get_description_for_extension(".zip").lower()

    def test_get_description_for_extension_without_dot(self):
        """Test getting descriptions without leading dot."""
        assert "image" in BinaryPatterns.get_description_for_extension("png").lower()


class TestFormatFileSize:
    """Test file size formatting."""

    def test_format_bytes(self):
        """Test formatting bytes."""
        assert format_file_size(512) == "512.0 B"
        assert format_file_size(1024) == "1.0 KB"

    def test_format_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(2048) == "2.0 KB"

    def test_format_megabytes(self):
        """Test formatting megabytes."""
        assert format_file_size(1048576) == "1.0 MB"
        assert format_file_size(1572864) == "1.5 MB"

    def test_format_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_file_size(1073741824) == "1.0 GB"
        assert format_file_size(1610612736) == "1.5 GB"

    def test_format_zero(self):
        """Test formatting zero bytes."""
        assert format_file_size(0) == "0.0 B"


class TestIsBinaryFile:
    """Test binary file detection."""

    def test_text_file_not_binary(self, tmp_path):
        """Test that text files are not detected as binary."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("Hello, world!\nThis is a text file.")

        is_bin, desc = is_binary_file(str(text_file))
        assert is_bin is False
        assert "text" in desc.lower()

    def test_binary_file_with_null_bytes(self, tmp_path):
        """Test that files with null bytes are detected as binary."""
        # Use an unusual extension to avoid extension-based detection
        binary_file = tmp_path / "test.dat"
        binary_file.write_bytes(b"Some text\x00with null\x00bytes")

        is_bin, desc = is_binary_file(str(binary_file))
        assert is_bin is True
        # Should be detected via null bytes or magic bytes
        assert is_bin

    def test_empty_file_not_binary(self, tmp_path):
        """Test that empty files are not considered binary."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        is_bin, desc = is_binary_file(str(empty_file))
        assert is_bin is False
        assert "empty" in desc.lower()

    def test_png_extension_binary(self, tmp_path):
        """Test that .png files are detected as binary by extension."""
        png_file = tmp_path / "image.png"
        png_file.write_bytes(b"fake png data")

        is_bin, desc = is_binary_file(str(png_file))
        assert is_bin is True
        assert "image" in desc.lower()

    def test_exe_extension_binary(self, tmp_path):
        """Test that .exe files are detected as binary by extension."""
        exe_file = tmp_path / "program.exe"
        exe_file.write_bytes(b"MZ\x90\x00fake exe data")

        is_bin, desc = is_binary_file(str(exe_file))
        assert is_bin is True
        assert "executable" in desc.lower()

    def test_zip_extension_binary(self, tmp_path):
        """Test that .zip files are detected as binary by extension."""
        zip_file = tmp_path / "archive.zip"
        zip_file.write_bytes(b"PK\x03\x04fake zip data")

        is_bin, desc = is_binary_file(str(zip_file))
        assert is_bin is True
        assert "archive" in desc.lower()

    def test_nonexistent_file_binary(self, tmp_path):
        """Test that nonexistent files are marked as binary."""
        nonexistent = tmp_path / "does_not_exist.txt"

        is_bin, desc = is_binary_file(str(nonexistent))
        assert is_bin is True
        assert "deleted" in desc.lower() or "not exist" in desc.lower()

    def test_utf8_text_file_not_binary(self, tmp_path):
        """Test that UTF-8 text files are not detected as binary."""
        utf8_file = tmp_path / "utf8.txt"
        utf8_file.write_text("Hello 世界 ñoño café", encoding="utf-8")

        is_bin, desc = is_binary_file(str(utf8_file))
        assert is_bin is False

    def test_invalid_utf8_binary(self, tmp_path):
        """Test that invalid UTF-8 is detected as binary."""
        invalid_utf8 = tmp_path / "invalid.txt"
        # Invalid UTF-8 sequence
        invalid_utf8.write_bytes(b"Hello\x80\x81\x82World")

        is_bin, desc = is_binary_file(str(invalid_utf8))
        assert is_bin is True


class TestIdentifyFromMagicBytes:
    """Test magic byte identification."""

    def test_identify_zip(self):
        """Test ZIP magic byte identification."""
        assert "archive" in identify_from_magic_bytes(b"PK\x03\x04").lower()

    def test_identify_png(self):
        """Test PNG magic byte identification."""
        assert "image" in identify_from_magic_bytes(b"\x89PNG").lower()

    def test_identify_jpeg(self):
        """Test JPEG magic byte identification."""
        # JPEG magic bytes: 0xFF 0xD8 0xFF
        jpeg_magic = bytes([0xFF, 0xD8, 0xFF])
        assert "image" in identify_from_magic_bytes(jpeg_magic).lower()

    def test_identify_elf(self):
        """Test ELF executable magic byte identification."""
        assert "executable" in identify_from_magic_bytes(b"\x7fELF").lower()

    def test_identify_mz(self):
        """Test MZ (Windows) executable magic byte identification."""
        assert "executable" in identify_from_magic_bytes(b"MZ").lower()

    def test_identify_gif(self):
        """Test GIF magic byte identification."""
        assert "image" in identify_from_magic_bytes(b"GIF8").lower()

    def test_identify_unknown(self):
        """Test identification of unknown magic bytes."""
        assert "binary" in identify_from_magic_bytes(b"UNKNO").lower()


class TestDetectBinaryFiles:
    """Test batch binary file detection."""

    def test_detect_multiple_files(self, tmp_path):
        """Test detecting multiple files at once."""
        # Create test files
        text_file = tmp_path / "text.txt"
        text_file.write_text("This is text")

        binary_file = tmp_path / "data.bin"
        binary_file.write_bytes(b"Binary\x00Data")

        image_file = tmp_path / "pic.png"
        image_file.write_bytes(b"fake image")

        binaries = detect_binary_files([str(text_file), str(binary_file), str(image_file)])

        assert len(binaries) == 2
        binary_paths = {b.file_path for b in binaries}
        assert str(binary_file) in binary_paths
        assert str(image_file) in binary_paths
        assert str(text_file) not in binary_paths

    def test_detect_deleted_files_skipped(self, tmp_path):
        """Test that deleted files are skipped during detection."""
        deleted_file = tmp_path / "deleted.txt"
        # File doesn't exist

        binaries = detect_binary_files([str(deleted_file)])
        assert len(binaries) == 0

    def test_detect_binary_file_attributes(self, tmp_path):
        """Test that DetectedBinary has correct attributes."""
        binary_file = tmp_path / "test.png"
        content = b"Some binary data here"
        binary_file.write_bytes(content)

        binaries = detect_binary_files([str(binary_file)])
        assert len(binaries) == 1

        detected = binaries[0]
        assert detected.file_path == str(binary_file)
        assert detected.file_size == len(content)
        assert detected.binary_type is not None
        assert "image" in detected.binary_type.lower()
        assert detected.extension == ".png"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
