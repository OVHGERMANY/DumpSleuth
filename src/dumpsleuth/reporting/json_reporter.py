"""
JSON reporter for DumpSleuth.

Outputs analysis results in JSON format.
"""

import json
from datetime import datetime
from typing import Any, Dict

from .base import Reporter


class JSONReporter(Reporter):
    """Reporter that outputs JSON format."""

    def format_report(self, data: Dict[str, Any]) -> str:
        """
        Format data as JSON.

        Args:
            data: Analysis results

        Returns:
            JSON string
        """
        # Add report metadata
        report = {
            "report_metadata": {
                "generator": "DumpSleuth",
                "format": "json",
                "generated_at": datetime.now().isoformat(),
                "version": "1.0",
            },
            "analysis_results": data,
        }

        # Pretty print by default
        indent = self.config.get("indent", 2)
        sort_keys = self.config.get("sort_keys", True)

        return json.dumps(report, indent=indent, sort_keys=sort_keys, default=str)

    def get_file_extension(self) -> str:
        """Get file extension."""
        return ".json"
