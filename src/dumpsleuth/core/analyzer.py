"""
Core analyzer module for DumpSleuth.

This module provides the main analysis engine that coordinates
plugins and generates comprehensive reports.
"""

import concurrent.futures
import logging
import mmap
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.config import Config, get_default_config
from ..core.parser import DumpParser


logger = logging.getLogger(__name__)


class AnalysisResult:
    """Container for analysis results."""

    def __init__(self):
        self.metadata = {"timestamp": datetime.now().isoformat(), "version": "1.0.0"}
        self.results = defaultdict(dict)
        self.errors = []
        self.warnings = []

    def add_result(self, plugin_name: str, data: Dict[str, Any]):
        """Add results from a plugin."""
        self.results[plugin_name] = data

    def add_error(self, plugin_name: str, error: Exception):
        """Record an error from a plugin."""
        self.errors.append(
            {"plugin": plugin_name, "error": str(error), "type": type(error).__name__}
        )

    def add_warning(self, plugin_name: str, warning: str):
        """Add a warning message."""
        self.warnings.append({"plugin": plugin_name, "warning": warning})

    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary format."""
        return {
            "metadata": self.metadata,
            "results": dict(self.results),
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def save(self, filepath: Union[str, Path], format: str = "json"):
        """Save results to file."""
        from ..reporting import get_reporter

        reporter = get_reporter(format)
        reporter.save(self.to_dict(), filepath)


class DumpAnalysisError(Exception):
    """Base exception for dump analysis."""

    pass


class CorruptedDumpError(DumpAnalysisError):
    """Raised when dump file is corrupted."""

    pass


class DumpAnalyzer:
    """Main analyzer class for processing memory dumps."""

    def __init__(
        self,
        dump_file: Union[str, Path],
        config: Optional[Union[str, Path, Config]] = None,
    ):
        """
        Initialize the analyzer.

        Args:
            dump_file: Path to the dump file
            config: Configuration object, path to config file, or None for defaults
        """
        self.dump_file = Path(dump_file)
        if not self.dump_file.exists():
            raise FileNotFoundError(f"Dump file not found: {dump_file}")

        # Load configuration
        if config is None:
            self.config = get_default_config()
        elif isinstance(config, (str, Path)):
            self.config = Config.from_file(config)
        else:
            self.config = config

        # Initialize plugin manager
        self.plugin_manager = PluginManager()
        self._load_default_plugins()

        # Initialize parser
        self.parser = DumpParser(self.dump_file, self.config)

        # Analysis state
        self.results = None

    def _load_default_plugins(self):
        """Load default plugins based on configuration."""
        # Import and register default plugins
        from ..extractors.network import NetworkExtractorPlugin
        from ..extractors.processes import ProcessExtractorPlugin
        from ..extractors.registry import RegistryExtractorPlugin
        from ..extractors.strings_plugin import StringsExtractorPlugin

        default_plugins = {
            'strings': StringsExtractorPlugin,
            'network': NetworkExtractorPlugin,
            'registry': RegistryExtractorPlugin,
            'processes': ProcessExtractorPlugin
        }

        enabled_plugins = self.config.get(
            "plugins.enabled", list(default_plugins.keys())
        )

        for plugin_name in enabled_plugins:
            if plugin_name in default_plugins:
                try:
                    plugin = default_plugins[plugin_name]()
                    self.plugin_manager.register(plugin)
                    logger.info(f"Loaded plugin: {plugin_name}")
                except Exception as e:
                    logger.error(f"Failed to load plugin {plugin_name}: {e}")

    def add_plugin(self, plugin: AnalyzerPlugin):
        """Add a custom plugin to the analyzer."""
        self.plugin_manager.register(plugin)
        logger.info(f"Added custom plugin: {plugin.get_name()}")

    def analyze(
        self, parallel: bool = None, recovery_mode: bool = False
    ) -> AnalysisResult:
        """
        Perform analysis on the dump file.

        Args:
            parallel: Whether to run plugins in parallel (None uses config value)
            recovery_mode: Try to recover from corrupted dumps

        Returns:
            AnalysisResult object containing all findings
        """
        if parallel is None:
            parallel = self.config.get("analysis.parallel_processing", True)

        logger.info(f"Starting analysis of {self.dump_file}")
        logger.info(f"File size: {self.dump_file.stat().st_size:,} bytes")

        # Create result container
        self.results = AnalysisResult()
        self.results.metadata["dump_file"] = str(self.dump_file)
        self.results.metadata["file_size"] = self.dump_file.stat().st_size

        try:
            # Parse dump file
            dump_data = self.parser.parse(recovery_mode=recovery_mode)
            self.results.metadata.update(dump_data.metadata)

            # Run plugins
            if parallel and len(self.plugin_manager.plugins) > 1:
                self._run_plugins_parallel(dump_data)
            else:
                self._run_plugins_sequential(dump_data)

        except CorruptedDumpError as e:
            if not recovery_mode:
                logger.error(f"Dump appears corrupted: {e}")
                raise
            else:
                logger.warning(f"Dump corrupted, attempting partial recovery: {e}")
                self.results.add_error("parser", e)

        logger.info(
            f"Analysis complete. Found {len(self.results.errors)} errors, "
            f"{len(self.results.warnings)} warnings"
        )

        return self.results

    def _run_plugins_sequential(self, dump_data):
        """Run plugins one by one."""
        for plugin in self.plugin_manager.plugins.values():
            plugin_name = plugin.get_name()
            logger.info(f"Running plugin: {plugin_name}")

            try:
                result = plugin.analyze(dump_data)
                self.results.add_result(plugin_name, result)
            except Exception as e:
                logger.error(f"Plugin {plugin_name} failed: {e}")
                self.results.add_error(plugin_name, e)

    def _run_plugins_parallel(self, dump_data):
        """Run plugins in parallel using thread pool."""
        max_workers = self.config.get("analysis.max_workers", 4)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all plugin tasks
            future_to_plugin = {
                executor.submit(plugin.analyze, dump_data): plugin
                for plugin in self.plugin_manager.plugins.values()
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_plugin):
                plugin = future_to_plugin[future]
                plugin_name = plugin.get_name()

                try:
                    result = future.result()
                    self.results.add_result(plugin_name, result)
                    logger.info(f"Plugin {plugin_name} completed")
                except Exception as e:
                    logger.error(f"Plugin {plugin_name} failed: {e}")
                    self.results.add_error(plugin_name, e)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the analysis results."""
        if not self.results:
            raise RuntimeError("No analysis has been performed yet")

        summary = {
            "dump_file": self.results.metadata.get("dump_file"),
            "file_size": self.results.metadata.get("file_size"),
            "analysis_time": self.results.metadata.get("timestamp"),
            "plugins_run": list(self.results.results.keys()),
            "error_count": len(self.results.errors),
            "warning_count": len(self.results.warnings),
        }

        # Add summary from each plugin
        for plugin_name, data in self.results.results.items():
            if "summary" in data:
                summary[f"{plugin_name}_summary"] = data["summary"]

        return summary
