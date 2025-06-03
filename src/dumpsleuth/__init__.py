"""
DumpSleuth - Modern Memory Dump Analysis Toolkit

A powerful, extensible framework for analyzing memory dumps with a focus on
ease of use, modularity, and beautiful reporting.
"""

__version__ = "2.0.0"
__author__ = "DumpSleuth Contributors"
__email__ = "contact@dumpsleuth.org"

# Core imports
from .core.analyzer import DumpAnalyzer, AnalysisResult, DumpAnalysisError, CorruptedDumpError
from .core.parser import DumpData, DumpParser
from .core.plugin import AnalyzerPlugin, PluginManager
from .core.config import Config, get_default_config

# Extractor plugins
from .extractors.strings_plugin import StringsExtractorPlugin
from .extractors.network import NetworkExtractorPlugin
from .extractors.registry import RegistryExtractorPlugin
from .extractors.processes import ProcessExtractorPlugin
from .extractors.pattern_matcher import PatternMatcher

# Reporting
from .reporting import get_reporter

# UI components
from .ui.cli import cli

__all__ = [
    # Core
    "DumpAnalyzer",
    "AnalysisResult",
    "AnalyzerPlugin",
    "PluginManager", 
    "Config",
    "get_default_config",
    "DumpData",
    "DumpParser",
    "DumpAnalysisError",
    "CorruptedDumpError",
    
    # Plugins
    "StringsExtractorPlugin",
    "NetworkExtractorPlugin",
    "RegistryExtractorPlugin",
    "ProcessExtractorPlugin",
    "PatternMatcher",
    
    # Reporting
    "get_reporter",
    
    # CLI
    "cli",
    
    # Metadata
    "__version__",
    "__author__",
]

# Convenience function for quick analysis
def analyze(dump_path: str, output_format: str = "html", config_path: str = None) -> str:
    """
    Quick analysis function for simple use cases.
    
    Args:
        dump_path: Path to the dump file
        output_format: Output format (html, json, markdown)
        config_path: Optional path to configuration file
        
    Returns:
        Path to the generated report
        
    Example:
        >>> import dumpsleuth
        >>> report = dumpsleuth.analyze("memory.dmp")
        >>> print(f"Report saved to: {report}")
    """
    analyzer = DumpAnalyzer(dump_path, config=config_path)
    results = analyzer.analyze()
    
    # Generate output filename
    from pathlib import Path
    dump_name = Path(dump_path).stem
    output_path = f"{dump_name}_report"
    
    results.save(output_path, format=output_format)
    return output_path