"""
Global path management for DumpSleuth.

This module provides centralized access to important directories
like dump file storage and temporary processing folders.
"""

import os
from pathlib import Path
from typing import Optional, Union


class DumpPaths:
    """Manages paths for dump file storage and processing."""

    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """
        Initialize dump paths manager.

        Args:
            base_path: Base directory for the project. If None, uses current working directory.
        """
        if base_path is None:
            # Try to find project root by looking for setup.py or pyproject.toml
            current = Path.cwd()
            while current != current.parent:
                if (current / "setup.py").exists() or (
                    current / "pyproject.toml"
                ).exists():
                    base_path = current
                    break
                current = current.parent
            else:
                # Fallback to current directory
                base_path = Path.cwd()

        self.base_path = Path(base_path).resolve()
        self._ensure_directories()

    @property
    def dumps_dir(self) -> Path:
        """Get the main dumps directory."""
        return self.base_path / "dumps"

    @property
    def temp_dir(self) -> Path:
        """Get the temporary processing directory."""
        return self.dumps_dir / "temp"

    @property
    def reports_dir(self) -> Path:
        """Get the reports output directory."""
        return self.base_path / "reports"

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for directory in [self.dumps_dir, self.temp_dir, self.reports_dir]:
            directory.mkdir(parents=True, exist_ok=True)

            # Create .gitkeep files if they don't exist
            gitkeep = directory / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()

    def get_dump_files(self, pattern: str = "*") -> list[Path]:
        """
        Get all dump files matching the pattern.

        Args:
            pattern: Glob pattern for file matching (default: "*")

        Returns:
            List of Path objects for matching dump files.
        """
        dump_extensions = [".dmp", ".dump", ".mdmp", ".hdmp", ".core"]
        files = []

        for ext in dump_extensions:
            files.extend(self.dumps_dir.glob(f"{pattern}{ext}"))

        # Also check for files without extensions that might be dumps
        if pattern == "*":
            for file in self.dumps_dir.iterdir():
                if (
                    file.is_file()
                    and file.suffix not in dump_extensions
                    and file.name != ".gitkeep"
                ):
                    files.append(file)

        return sorted(files)

    def get_temp_file(self, name: str) -> Path:
        """
        Get a path for a temporary file.

        Args:
            name: Name for the temporary file

        Returns:
            Path object for the temporary file.
        """
        return self.temp_dir / name

    def clean_temp(self) -> None:
        """Remove all files from the temp directory."""
        for file in self.temp_dir.iterdir():
            if file.is_file() and file.name != ".gitkeep":
                file.unlink()

    def get_report_path(self, name: str, format: str = "html") -> Path:
        """
        Get a path for a report file.

        Args:
            name: Base name for the report
            format: Report format (html, json, md)

        Returns:
            Path object for the report file.
        """
        timestamp = Path(name).stem  # Remove any existing extension
        return self.reports_dir / f"{timestamp}.{format}"


# Global instance for easy access
_paths_instance: Optional[DumpPaths] = None


def get_dump_paths() -> DumpPaths:
    """Get the global DumpPaths instance."""
    global _paths_instance
    if _paths_instance is None:
        _paths_instance = DumpPaths()
    return _paths_instance


def set_base_path(path: Union[str, Path]) -> None:
    """
    Set a custom base path for the dump paths.

    Args:
        path: New base path to use
    """
    global _paths_instance
    _paths_instance = DumpPaths(path)


# Convenience functions for direct access
def get_dumps_dir() -> Path:
    """Get the dumps directory path."""
    return get_dump_paths().dumps_dir


def get_temp_dir() -> Path:
    """Get the temp directory path."""
    return get_dump_paths().temp_dir


def get_temp_file(name: str) -> Path:
    """Get a temp file path."""
    return get_dump_paths().get_temp_file(name)


def clean_temp() -> None:
    """Clean the temp directory."""
    get_dump_paths().clean_temp()


def list_dump_files(pattern: str = "*") -> list[Path]:
    """List all dump files in the dumps directory."""
    return get_dump_paths().get_dump_files(pattern)
