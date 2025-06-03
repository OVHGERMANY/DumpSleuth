"""
Markdown reporter for DumpSleuth.

Generates human-readable reports in Markdown format.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

from .base import Reporter


class MarkdownReporter(Reporter):
    """Reporter that outputs Markdown format."""

    def format_report(self, data: Dict[str, Any]) -> str:
        """
        Format data as Markdown.

        Args:
            data: Analysis results

        Returns:
            Markdown string
        """
        sections = []

        # Header
        sections.append(self._format_header(data))

        # Metadata
        if "metadata" in data:
            sections.append(self._format_metadata(data["metadata"]))

        # Results by plugin
        if "results" in data:
            for plugin_name, plugin_data in data["results"].items():
                sections.append(self._format_plugin_results(plugin_name, plugin_data))

        # Errors and warnings
        if "errors" in data and data["errors"]:
            sections.append(self._format_errors(data["errors"]))

        if "warnings" in data and data["warnings"]:
            sections.append(self._format_warnings(data["warnings"]))

        return "\n\n".join(sections)

    def get_file_extension(self) -> str:
        """Get file extension."""
        return ".md"

    def _format_header(self, data: Dict[str, Any]) -> str:
        """Format report header."""
        lines = [
            "# DumpSleuth Analysis Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**DumpSleuth Version:** {data.get('metadata', {}).get('version', 'Unknown')}",
        ]

        if "metadata" in data and "dump_file" in data["metadata"]:
            lines.append(f"**Dump File:** `{data['metadata']['dump_file']}`")

        return "\n".join(lines)

    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format dump metadata section."""
        lines = ["## Dump Information"]

        # Format metadata as table
        lines.append("")
        lines.append("| Property | Value |")
        lines.append("|----------|-------|")

        for key, value in metadata.items():
            if key != "dump_file":  # Already in header
                formatted_key = key.replace("_", " ").title()
                formatted_value = self._format_value(value)
                lines.append(f"| {formatted_key} | {formatted_value} |")

        return "\n".join(lines)

    def _format_plugin_results(self, plugin_name: str, data: Dict[str, Any]) -> str:
        """Format results from a single plugin."""
        lines = [f"## {plugin_name.title()} Analysis"]

        # Summary first
        if "summary" in data:
            lines.append("")
            lines.append("### Summary")
            lines.extend(self._format_summary(data["summary"]))

        # Main results
        for key, value in data.items():
            if key == "summary":
                continue

            lines.append("")
            lines.append(f"### {key.replace('_', ' ').title()}")

            if isinstance(value, list):
                lines.extend(self._format_list(value))
            elif isinstance(value, dict):
                lines.extend(self._format_dict(value))
            else:
                lines.append(str(value))

        return "\n".join(lines)

    def _format_summary(self, summary: Dict[str, Any]) -> List[str]:
        """Format summary data."""
        lines = []

        for key, value in summary.items():
            formatted_key = key.replace("_", " ").title()

            if isinstance(value, (list, dict)) and value:
                lines.append(f"\n**{formatted_key}:**")
                if isinstance(value, list):
                    lines.extend(self._format_list(value))
                else:
                    lines.extend(self._format_dict(value))
            else:
                lines.append(f"- **{formatted_key}:** {self._format_value(value)}")

        return lines

    def _format_list(self, items: List[Any], indent: int = 0) -> List[str]:
        """Format a list."""
        lines = []
        prefix = "  " * indent

        for item in items:
            if isinstance(item, dict):
                # Format dict items as sub-items
                first_key = True
                for key, value in item.items():
                    if first_key:
                        lines.append(f"{prefix}- {key}: {self._format_value(value)}")
                        first_key = False
                    else:
                        lines.append(f"{prefix}  {key}: {self._format_value(value)}")
            else:
                lines.append(f"{prefix}- {self._format_value(item)}")

        return lines

    def _format_dict(self, data: Dict[str, Any], indent: int = 0) -> List[str]:
        """Format a dictionary."""
        lines = []
        prefix = "  " * indent

        for key, value in data.items():
            formatted_key = key.replace("_", " ").title()

            if isinstance(value, list) and value:
                lines.append(f"{prefix}- **{formatted_key}:**")
                lines.extend(self._format_list(value, indent + 1))
            elif isinstance(value, dict) and value:
                lines.append(f"{prefix}- **{formatted_key}:**")
                lines.extend(self._format_dict(value, indent + 1))
            else:
                lines.append(
                    f"{prefix}- **{formatted_key}:** {self._format_value(value)}"
                )

        return lines

    def _format_value(self, value: Any) -> str:
        """Format a single value."""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, (int, float)):
            # Format large numbers with commas
            if isinstance(value, int) and value > 1000:
                return f"{value:,}"
            return str(value)
        elif isinstance(value, str):
            # Escape markdown special characters if needed
            if any(c in value for c in ["*", "_", "`", "[", "]"]):
                return f"`{value}`"
            return value
        else:
            return str(value)

    def _format_errors(self, errors: List[Dict[str, Any]]) -> str:
        """Format errors section."""
        lines = ["## ⚠️ Errors"]
        lines.append("")

        for error in errors:
            plugin = error.get("plugin", "Unknown")
            error_type = error.get("type", "Error")
            message = error.get("error", "Unknown error")

            lines.append(f"- **{plugin}** ({error_type}): {message}")

        return "\n".join(lines)

    def _format_warnings(self, warnings: List[Dict[str, Any]]) -> str:
        """Format warnings section."""
        lines = ["## ⚡ Warnings"]
        lines.append("")

        for warning in warnings:
            plugin = warning.get("plugin", "Unknown")
            message = warning.get("warning", "Unknown warning")

            lines.append(f"- **{plugin}**: {message}")

        return "\n".join(lines)
