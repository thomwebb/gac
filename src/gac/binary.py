#!/usr/bin/env python3
"""Binary file detection utilities for gac.

This module provides functions to detect binary files in staged changes,
preventing accidental commits of compiled files, images, and other binary assets.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DetectedBinary:
    """Represents a detected binary file."""

    file_path: str
    file_size: int
    binary_type: str
    extension: str | None = None
    description: str | None = None


class BinaryPatterns:
    """Common binary file extensions and patterns."""

    # Compiled executables
    EXECUTABLE_EXTENSIONS = {
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".bin",
        ".o",
        ".obj",
        ".lib",
        ".a",
        ".out",
        ".app",
        ".elf",
    }

    # Common data formats
    DATA_EXTENSIONS = {
        ".zip",
        ".tar",
        ".gz",
        ".bz2",
        ".7z",
        ".rar",
        ".xz",
        ".zst",
    }

    # Images
    IMAGE_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".ico",
        ".tiff",
        ".webp",
        ".psd",
        ".raw",
        ".heic",
    }

    # Audio/Video
    MEDIA_EXTENSIONS = {
        ".mp3",
        ".wav",
        ".ogg",
        ".flac",
        ".m4a",
        ".aac",
        ".wma",
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
    }

    # Fonts
    FONT_EXTENSIONS = {
        ".ttf",
        ".otf",
        ".woff",
        ".woff2",
        ".eot",
    }

    # Documents (binary)
    DOCUMENT_EXTENSIONS = {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".odt",
        ".ods",
        ".odp",
    }

    # Database files
    DATABASE_EXTENSIONS = {
        ".db",
        ".sqlite",
        ".sqlite3",
        ".mdb",
        ".accdb",
    }

    # Java compiled
    JAVA_EXTENSIONS = {".class", ".jar", ".war", ".ear"}

    # Python compiled
    PYTHON_EXTENSIONS = {".pyc", ".pyd", ".pyo"}

    # .NET compiled
    DOTNET_EXTENSIONS = {".dll", ".exe", ".pdb"}

    # Other compiled
    COMPILED_EXTENSIONS = {
        ".pyc",
        ".pyo",
        ".pyd",
        ".class",
        ".jar",
        ".war",
        ".ear",
        ".beam",
        ".erl",
        ".hi",
        ".o",
        ".so",
        ".a",
        ".lib",
        ".obj",
        ".pdb",
        ".idb",
        ".pch",
    }

    # All binary extensions (union of all above, duplicates removed)
    ALL_BINARY_EXTENSIONS = (
        EXECUTABLE_EXTENSIONS
        | DATA_EXTENSIONS
        | IMAGE_EXTENSIONS
        | MEDIA_EXTENSIONS
        | FONT_EXTENSIONS
        | DOCUMENT_EXTENSIONS
        | DATABASE_EXTENSIONS
        | JAVA_EXTENSIONS
        | PYTHON_EXTENSIONS
        | DOTNET_EXTENSIONS
        | COMPILED_EXTENSIONS
    )

    # Git lfs lock files and pointers
    GIT_LFS_PATTERNS = {".gitattributes", ".git-lfs"}

    # Files that should be considered binary even if they don't match extensions
    SUSPECT_BY_NAME = {
        "node_modules",
        ".DS_Store",
        "Thumbs.db",
        "desktop.ini",
    } | GIT_LFS_PATTERNS

    @classmethod
    def get_description_for_extension(cls, ext: str) -> str:
        """Get a human-readable description for a binary file extension.

        Args:
            ext: The file extension (with or without leading dot)

        Returns:
            Human-readable description
        """
        ext = ext.lower()
        if not ext.startswith("."):
            ext = f".{ext}"

        categories = [
            (BinaryPatterns.EXECUTABLE_EXTENSIONS, "Compiled executable"),
            (BinaryPatterns.DATA_EXTENSIONS, "Compressed archive"),
            (BinaryPatterns.IMAGE_EXTENSIONS, "Image file"),
            (BinaryPatterns.MEDIA_EXTENSIONS, "Media file (audio/video)"),
            (BinaryPatterns.FONT_EXTENSIONS, "Font file"),
            (BinaryPatterns.DOCUMENT_EXTENSIONS, "Document file"),
            (BinaryPatterns.DATABASE_EXTENSIONS, "Database file"),
            (BinaryPatterns.JAVA_EXTENSIONS, "Java compiled/class file"),
            (BinaryPatterns.PYTHON_EXTENSIONS, "Python compiled bytecode"),
            (BinaryPatterns.DOTNET_EXTENSIONS, ".NET compiled assembly"),
        ]

        for pattern_set, description in categories:
            if ext in pattern_set:
                return description

        return "Binary file"


def is_binary_file(file_path: str, file_size: int | None = None) -> tuple[bool, str]:
    """Check if a file is binary.

    This uses multiple detection methods:
    1. Null byte detection (most reliable for non-empty files)
    2. Extension-based detection for known binary types
    3. Heuristic checking for UTF-8 validity

    Args:
        file_path: Path to the file to check
        file_size: Optional file size in bytes (saves a stat call if provided)

    Returns:
        Tuple of (is_binary, description)
    """
    path = Path(file_path)

    # Check if file exists
    if not path.exists():
        return True, "File does not exist (likely deleted)"

    # Get file size if not provided
    if file_size is None:
        try:
            file_size = path.stat().st_size
        except OSError:
            return True, "Could not determine file status"

    # Empty files are not binaries (they can't be detected as such)
    if file_size == 0:
        return False, "Empty file"

    # Check extension first (faster and more reliable for known types
    ext = path.suffix.lower()
    if ext in BinaryPatterns.ALL_BINARY_EXTENSIONS:
        description = BinaryPatterns.get_description_for_extension(ext)
        return True, description

    # Check suspect filenames
    if path.name in BinaryPatterns.SUSPECT_BY_NAME:
        return True, f"Suspicious file: {path.name}"

    # Check for null bytes (reliable binary detection)
    try:
        with path.open("rb") as f:
            chunk = f.read(1024)  # Read first KB
            if b"\x00" in chunk:
                # Try to identify type from magic bytes
                return True, identify_from_magic_bytes(chunk)
    except OSError:
        return True, "Could not read file"

    # Check if file is valid UTF-8 (text files should be UTF-8 or ASCII)
    try:
        with path.open("r", encoding="utf-8") as f:
            f.read(1024)
        return False, "Text file"
    except UnicodeDecodeError:
        return True, "Binary file (not valid UTF-8)"


def identify_from_magic_bytes(data: bytes) -> str:
    """Identify file type from magic bytes (file signature).

    Args:
        data: First kilobyte of file data

    Returns:
        Human-readable file type description
    """
    if len(data) < 2:
        return "Binary file"

    # Check common magic bytes with exact match
    magic_signatures = [
        (b"\x50\x4b\x03\x04", "ZIP archive"),
        (b"\x50\x4b\x05\x06", "ZIP archive"),
        (b"\x1f\x8b\x08", "GZIP archive"),
        (b"Rar!", "RAR archive"),
        (b"\x7fELF", "ELF executable"),
        (b"MZ", "Windows executable"),
        (b"PK\x03\x04", "ZIP archive"),
        (b"PDF", "PDF document"),
        (b"%PDF", "PDF document"),
        (b"\x89PNG", "PNG image"),
        (b"GIF8", "GIF image"),
        (b"RIFF", "RIFF container (likely audio/video)"),
        (b"id3", "MP3 audio file"),
    ]

    for signature, description in magic_signatures:
        if data.startswith(signature):
            return description

    # JPEG magic byte (starts with \xff\xd8\xff, any 4th byte)
    if len(data) >= 3 and data[:3] == bytes([0xFF, 0xD8, 0xFF]):
        return "JPEG image"

    return "Binary file"


def detect_binary_files(file_paths: list[str]) -> list[DetectedBinary]:
    """Detect binary files in a list of file paths.

    Args:
        file_paths: List of file paths to check

    Returns:
        List of detected binary files
    """
    binaries: list[DetectedBinary] = []

    for file_path in file_paths:
        path = Path(file_path)

        if not path.exists():
            # File was deleted, skip binary check
            continue

        # Get file size
        try:
            file_size = path.stat().st_size
        except OSError:
            logger.warning(f"Could not stat file: {file_path}")
            continue

        is_binary, description = is_binary_file(file_path, file_size)

        if is_binary:
            ext = path.suffix
            binary_type = description

            binaries.append(
                DetectedBinary(
                    file_path=file_path,
                    file_size=file_size,
                    binary_type=binary_type,
                    extension=ext if ext else None,
                    description=description,
                )
            )

    logger.info(f"Binary detection complete: found {len(binaries)} binary file(s)")
    return binaries


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"
