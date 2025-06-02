"""
Reporting module for DumpSleuth.

Provides various report formats including HTML, JSON, and Markdown.
"""

from typing import Dict, Any

from .base import Reporter
from .json_reporter import JSONReporter
from .html_reporter import HTMLReporter
from .markdown_reporter import MarkdownReporter


# Registry of available reporters
REPORTERS = {
    'json': JSONReporter,
    'html': HTMLReporter,
    'markdown': MarkdownReporter,
    'md': MarkdownReporter,  # Alias
}


def get_reporter(format: str) -> Reporter:
    """
    Get a reporter instance for the specified format.
    
    Args:
        format: Report format ('json', 'html', 'markdown', 'md')
        
    Returns:
        Reporter instance
        
    Raises:
        ValueError: If format is not supported
    """
    format = format.lower()
    if format not in REPORTERS:
        raise ValueError(
            f"Unsupported report format: {format}. "
            f"Available formats: {', '.join(REPORTERS.keys())}"
        )
        
    return REPORTERS[format]()


__all__ = [
    'Reporter',
    'JSONReporter', 
    'HTMLReporter',
    'MarkdownReporter',
    'get_reporter'
] 