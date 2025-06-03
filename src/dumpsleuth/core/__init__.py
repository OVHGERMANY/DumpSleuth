"""
DumpSleuth Core Module

This module provides the core functionality for memory dump analysis.
"""

from .analyzer import AnalysisResult, DumpAnalyzer
from .config import Config, ConfigManager
from .paths import (
    DumpPaths,
    clean_temp,
    get_dump_paths,
    get_dumps_dir,
    get_temp_dir,
    get_temp_file,
    list_dump_files,
    set_base_path,
)
from .plugin import AnalyzerPlugin, PluginManager

__all__ = [
    # Analyzer
    "DumpAnalyzer",
    "AnalysisResult",
    # Configuration
    "ConfigManager",
    "Config",
    # Plugins
    "PluginManager",
    "AnalyzerPlugin",
    # Paths
    "DumpPaths",
    "get_dump_paths",
    "get_dumps_dir",
    "get_temp_dir",
    "get_temp_file",
    "clean_temp",
    "list_dump_files",
    "set_base_path",
]
