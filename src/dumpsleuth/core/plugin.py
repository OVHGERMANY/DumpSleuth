"""
Plugin architecture for DumpSleuth
"""

import importlib.util
import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PluginMetadata:
    """Metadata for a plugin"""

    name: str
    version: str
    author: str
    description: str
    tags: List[str]


class AnalyzerPlugin(ABC):
    """Base class for all analyzer plugins"""

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass

    @abstractmethod
    def analyze(self, data: bytes, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the provided data.

        Args:
            data: Raw bytes from the dump file
            context: Additional context (file info, config, etc.)

        Returns:
            Dictionary containing analysis results
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return list of supported dump formats"""
        pass

    def validate_data(self, data: bytes) -> bool:
        """Validate if this plugin can handle the data"""
        return True

    def get_priority(self) -> int:
        """Return plugin priority (higher = runs first)"""
        return 0


class PluginManager:
    """Manages loading and execution of plugins"""

    def __init__(self):
        self.plugins: Dict[str, AnalyzerPlugin] = {}
        self.enabled_plugins: List[str] = []

    def register_plugin(self, plugin: AnalyzerPlugin) -> None:
        """Register a plugin instance"""
        metadata = plugin.get_metadata()
        self.plugins[metadata.name] = plugin

    def load_plugins_from_directory(self, directory: Path) -> None:
        """Load all plugins from a directory"""
        for file in directory.glob("*.py"):
            if file.name.startswith("_"):
                continue

            module_name = file.stem
            spec = importlib.util.spec_from_file_location(module_name, file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find all plugin classes in the module
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, AnalyzerPlugin)
                    and obj != AnalyzerPlugin
                ):
                    self.register_plugin(obj())

    def enable_plugin(self, plugin_name: str) -> None:
        """Enable a plugin"""
        if plugin_name in self.plugins:
            self.enabled_plugins.append(plugin_name)

    def disable_plugin(self, plugin_name: str) -> None:
        """Disable a plugin"""
        if plugin_name in self.enabled_plugins:
            self.enabled_plugins.remove(plugin_name)

    def get_enabled_plugins(self) -> List[AnalyzerPlugin]:
        """Get list of enabled plugins sorted by priority"""
        plugins = [
            self.plugins[name] for name in self.enabled_plugins if name in self.plugins
        ]
        return sorted(plugins, key=lambda p: p.get_priority(), reverse=True)

    def run_analysis(self, data: bytes, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run all enabled plugins on the data"""
        results = {}

        for plugin in self.get_enabled_plugins():
            metadata = plugin.get_metadata()

            try:
                if plugin.validate_data(data):
                    plugin_results = plugin.analyze(data, context)
                    results[metadata.name] = {
                        "metadata": metadata,
                        "results": plugin_results,
                        "success": True,
                    }
                else:
                    results[metadata.name] = {
                        "metadata": metadata,
                        "results": {},
                        "success": False,
                        "error": "Data validation failed",
                    }
            except Exception as e:
                results[metadata.name] = {
                    "metadata": metadata,
                    "results": {},
                    "success": False,
                    "error": str(e),
                }

        return results
