"""
DumpSleuth Core Module

This module provides the core functionality for memory dump analysis.
"""

from .analyzer import DumpAnalyzer, AnalysisResult
from .config import ConfigManager, Config
from .plugin import PluginManager, AnalyzerPlugin
from .paths import (
    DumpPaths,
    get_dump_paths,
    get_dumps_dir,
    get_temp_dir,
    get_temp_file,
    clean_temp,
    list_dump_files,
    set_base_path
)

__all__ = [
    # Analyzer
    'DumpAnalyzer',
    'AnalysisResult',
    
    # Configuration
    'ConfigManager',
    'Config',
    
    # Plugins
    'PluginManager',
    'AnalyzerPlugin',
    
    # Paths
    'DumpPaths',
    'get_dump_paths',
    'get_dumps_dir',
    'get_temp_dir',
    'get_temp_file',
    'clean_temp',
    'list_dump_files',
    'set_base_path',
] 