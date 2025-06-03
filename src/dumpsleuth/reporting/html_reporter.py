"""
HTML reporter for DumpSleuth.

Generates interactive HTML reports with a modern UI.
"""

import html
import json
from datetime import datetime
from typing import Any, Dict, List

from .base import Reporter


class HTMLReporter(Reporter):
    """Reporter that outputs interactive HTML format."""

    def format_report(self, data: Dict[str, Any]) -> str:
        """
        Format data as HTML.

        Args:
            data: Analysis results

        Returns:
            HTML string
        """
        # Build the complete HTML document
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DumpSleuth Analysis Report</title>
    {self._get_styles()}
    {self._get_scripts()}
</head>
<body>
    <div class="container">
        {self._format_header(data)}
        {self._format_nav(data)}
        <div class="content">
            {self._format_overview(data)}
            {self._format_results(data)}
            {self._format_errors_warnings(data)}
        </div>
        {self._format_footer()}
    </div>
    {self._get_inline_scripts(data)}
</body>
</html>"""

    def get_file_extension(self) -> str:
        """Get file extension."""
        return ".html"

    def _get_styles(self) -> str:
        """Get CSS styles."""
        return """
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        line-height: 1.6;
        color: #333;
        background-color: #f5f7fa;
    }

    .container {
        max-width: 1200px;
        margin: 0 auto;
        background-color: white;
        min-height: 100vh;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
    }

    /* Header */
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        position: relative;
        overflow: hidden;
    }

    .header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 320"><path fill="%23ffffff" fill-opacity="0.1" d="M0,32L48,37.3C96,43,192,53,288,90.7C384,128,480,192,576,192C672,192,768,128,864,117.3C960,107,1056,149,1152,165.3C1248,181,1344,171,1392,165.3L1440,160L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"></path></svg>') no-repeat bottom;
        background-size: cover;
    }

    .header-content {
        position: relative;
        z-index: 1;
    }

    .header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }

    .header .meta {
        opacity: 0.9;
        font-size: 0.95rem;
    }

    .header .meta-item {
        display: inline-block;
        margin-right: 2rem;
        margin-top: 0.5rem;
    }

    /* Navigation */
    .nav {
        background-color: #f8f9fa;
        padding: 1rem 2rem;
        border-bottom: 1px solid #e9ecef;
        position: sticky;
        top: 0;
        z-index: 100;
    }

    .nav-pills {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }

    .nav-pill {
        padding: 0.5rem 1rem;
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 0.9rem;
        text-decoration: none;
        color: #333;
    }

    .nav-pill:hover {
        background-color: #667eea;
        color: white;
        border-color: #667eea;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(102, 126, 234, 0.2);
    }

    .nav-pill.active {
        background-color: #667eea;
        color: white;
        border-color: #667eea;
    }

    /* Content */
    .content {
        padding: 2rem;
    }

    .section {
        margin-bottom: 3rem;
        display: none;
    }

    .section.active {
        display: block;
    }

    .section-header {
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e9ecef;
    }

    .section-icon {
        font-size: 1.5rem;
        margin-right: 0.75rem;
    }

    .section h2 {
        color: #495057;
        font-size: 1.75rem;
        font-weight: 600;
    }

    /* Cards */
    .card {
        background-color: white;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }

    .card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }

    .card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #495057;
        margin-bottom: 1rem;
    }

    /* Stats Grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 8px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    .stat-card::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    }

    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Tables */
    .table-wrapper {
        overflow-x: auto;
        margin-bottom: 1.5rem;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.95rem;
    }

    th, td {
        padding: 0.75rem;
        text-align: left;
        border-bottom: 1px solid #e9ecef;
    }

    th {
        background-color: #f8f9fa;
        font-weight: 600;
        color: #495057;
        position: sticky;
        top: 0;
    }

    tr:hover {
        background-color: #f8f9fa;
    }

    /* Code blocks */
    .code-block {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 4px;
        padding: 1rem;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 0.9rem;
        overflow-x: auto;
        margin-bottom: 1rem;
    }

    /* Alerts */
    .alert {
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
    }

    .alert-icon {
        font-size: 1.25rem;
        margin-right: 0.75rem;
    }

    .alert-error {
        background-color: #fee;
        color: #c53030;
        border: 1px solid #feb2b2;
    }

    .alert-warning {
        background-color: #fffaf0;
        color: #c05621;
        border: 1px solid #feb2b2;
    }

    .alert-info {
        background-color: #e6f3ff;
        color: #2c5aa0;
        border: 1px solid #bee3f8;
    }

    /* Lists */
    .styled-list {
        list-style: none;
        padding: 0;
    }

    .styled-list li {
        padding: 0.5rem 0;
        padding-left: 1.5rem;
        position: relative;
    }

    .styled-list li:before {
        content: '▸';
        position: absolute;
        left: 0;
        color: #667eea;
        font-weight: 700;
    }

    /* Search */
    .search-box {
        position: relative;
        margin-bottom: 1.5rem;
    }

    .search-input {
        width: 100%;
        padding: 0.75rem 1rem;
        padding-left: 3rem;
        border: 1px solid #e9ecef;
        border-radius: 25px;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }

    .search-input:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    .search-icon {
        position: absolute;
        left: 1rem;
        top: 50%;
        transform: translateY(-50%);
        color: #adb5bd;
    }

    /* Footer */
    .footer {
        background-color: #f8f9fa;
        padding: 2rem;
        text-align: center;
        color: #6c757d;
        border-top: 1px solid #e9ecef;
    }

    /* Animations */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .header h1 {
            font-size: 1.75rem;
        }

        .stats-grid {
            grid-template-columns: 1fr;
        }

        .nav-pills {
            justify-content: center;
        }
    }
</style>
"""

    def _get_scripts(self) -> str:
        """Get JavaScript functions."""
        return """
<script>
    function showSection(sectionId) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });

        // Remove active class from all nav pills
        document.querySelectorAll('.nav-pill').forEach(pill => {
            pill.classList.remove('active');
        });

        // Show selected section
        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.add('active');
            section.classList.add('fade-in');
        }

        // Add active class to clicked nav pill
        const pill = document.querySelector(`[onclick="showSection('${sectionId}')"]`);
        if (pill) {
            pill.classList.add('active');
        }
    }

    function searchInTables(query) {
        const tables = document.querySelectorAll('table');
        tables.forEach(table => {
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(query.toLowerCase())) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Initialize
    document.addEventListener('DOMContentLoaded', function() {
        showSection('overview');
    });
</script>
"""

    def _format_header(self, data: Dict[str, Any]) -> str:
        """Format header section."""
        metadata = data.get("metadata", {})

        return f"""
<div class="header">
    <div class="header-content">
        <h1>🔍 DumpSleuth Analysis Report</h1>
        <div class="meta">
            <div class="meta-item">📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            <div class="meta-item">📄 File: {html.escape(metadata.get('dump_file', 'Unknown'))}</div>
            <div class="meta-item">💾 Size: {self._format_size(metadata.get('file_size', 0))}</div>
            <div class="meta-item">🏷️ Format: {html.escape(metadata.get('format', 'Unknown'))}</div>
        </div>
    </div>
</div>
"""

    def _format_nav(self, data: Dict[str, Any]) -> str:
        """Format navigation section."""
        nav_items = ["overview"]

        if "results" in data:
            nav_items.extend(data["results"].keys())

        if data.get("errors") or data.get("warnings"):
            nav_items.append("issues")

        pills = []
        for item in nav_items:
            label = item.replace("_", " ").title()
            pills.append(
                f'<a class="nav-pill" onclick="showSection(\'{item}\')">{label}</a>'
            )

        return f"""
<div class="nav">
    <div class="nav-pills">
        {' '.join(pills)}
    </div>
</div>
"""

    def _format_overview(self, data: Dict[str, Any]) -> str:
        """Format overview section."""
        metadata = data.get("metadata", {})
        results = data.get("results", {})

        # Calculate stats
        total_findings = sum(
            len(plugin_data.get(key, []))
            for plugin_data in results.values()
            for key in plugin_data
            if isinstance(plugin_data.get(key), list)
        )

        return f"""
<div id="overview" class="section active">
    <div class="section-header">
        <span class="section-icon">📊</span>
        <h2>Overview</h2>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{len(results)}</div>
            <div class="stat-label">Plugins Run</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{total_findings}</div>
            <div class="stat-label">Total Findings</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(data.get('errors', []))}</div>
            <div class="stat-label">Errors</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(data.get('warnings', []))}</div>
            <div class="stat-label">Warnings</div>
        </div>
    </div>

    <div class="card">
        <div class="card-title">Analysis Summary</div>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Plugin</th>
                        <th>Status</th>
                        <th>Key Findings</th>
                    </tr>
                </thead>
                <tbody>
                    {self._format_summary_rows(results)}
                </tbody>
            </table>
        </div>
    </div>
</div>
"""

    def _format_results(self, data: Dict[str, Any]) -> str:
        """Format all plugin results."""
        results = data.get("results", {})
        sections = []

        for plugin_name, plugin_data in results.items():
            sections.append(self._format_plugin_section(plugin_name, plugin_data))

        return "\n".join(sections)

    def _format_plugin_section(self, plugin_name: str, data: Dict[str, Any]) -> str:
        """Format a single plugin's results."""
        content_parts = []

        # Summary card if available
        if "summary" in data:
            content_parts.append(self._format_summary_card(data["summary"]))

        # Format other data
        for key, value in data.items():
            if key == "summary":
                continue

            if isinstance(value, list) and value:
                content_parts.append(self._format_list_card(key, value))
            elif isinstance(value, dict) and value:
                content_parts.append(self._format_dict_card(key, value))

        return f"""
<div id="{plugin_name}" class="section">
    <div class="section-header">
        <span class="section-icon">{self._get_plugin_icon(plugin_name)}</span>
        <h2>{plugin_name.replace('_', ' ').title()}</h2>
    </div>

    <div class="search-box">
        <span class="search-icon">🔍</span>
        <input type="text" class="search-input" placeholder="Search in this section..."
               onkeyup="searchInTables(this.value)">
    </div>

    {' '.join(content_parts)}
</div>
"""

    def _format_summary_card(self, summary: Dict[str, Any]) -> str:
        """Format summary data as a card."""
        items = []

        for key, value in summary.items():
            formatted_key = key.replace("_", " ").title()
            formatted_value = self._format_value(value)

            if isinstance(value, bool):
                icon = "✅" if value else "❌"
                items.append(
                    f"<li>{icon} <strong>{formatted_key}:</strong> {formatted_value}</li>"
                )
            else:
                items.append(
                    f"<li><strong>{formatted_key}:</strong> {formatted_value}</li>"
                )

        return f"""
<div class="card">
    <div class="card-title">Summary</div>
    <ul class="styled-list">
        {' '.join(items)}
    </ul>
</div>
"""

    def _format_list_card(self, title: str, items: List[Any]) -> str:
        """Format list data as a card with table."""
        if not items:
            return ""

        # Check if items are dictionaries
        if isinstance(items[0], dict):
            # Create table
            headers = list(items[0].keys())

            header_row = "".join(
                f'<th>{h.replace("_", " ").title()}</th>' for h in headers
            )

            rows = []
            for item in items[:100]:  # Limit to first 100 items
                cells = "".join(
                    f'<td>{html.escape(str(item.get(h, "")))}</td>' for h in headers
                )
                rows.append(f"<tr>{cells}</tr>")

            return f"""
<div class="card">
    <div class="card-title">{title.replace('_', ' ').title()} ({len(items)} items)</div>
    <div class="table-wrapper">
        <table>
            <thead>
                <tr>{header_row}</tr>
            </thead>
            <tbody>
                {' '.join(rows)}
            </tbody>
        </table>
    </div>
</div>
"""
        else:
            # Simple list
            list_items = [
                f"<li>{html.escape(str(item))}</li>"
                for item in items[:50]  # Limit display
            ]

            return f"""
<div class="card">
    <div class="card-title">{title.replace('_', ' ').title()} ({len(items)} items)</div>
    <ul class="styled-list">
        {' '.join(list_items)}
    </ul>
    {f'<p><em>... and {len(items) - 50} more items</em></p>' if len(items) > 50 else ''}
</div>
"""

    def _format_dict_card(self, title: str, data: Dict[str, Any]) -> str:
        """Format dictionary data as a card."""
        items = []

        for key, value in data.items():
            formatted_key = key.replace("_", " ").title()
            formatted_value = self._format_value(value)
            items.append(
                f"<li><strong>{formatted_key}:</strong> {formatted_value}</li>"
            )

        return f"""
<div class="card">
    <div class="card-title">{title.replace('_', ' ').title()}</div>
    <ul class="styled-list">
        {' '.join(items)}
    </ul>
</div>
"""

    def _format_errors_warnings(self, data: Dict[str, Any]) -> str:
        """Format errors and warnings section."""
        errors = data.get("errors", [])
        warnings = data.get("warnings", [])

        if not errors and not warnings:
            return ""

        error_items = [
            f"""<div class="alert alert-error">
                <span class="alert-icon">❌</span>
                <div>
                    <strong>{error.get('plugin', 'Unknown')}</strong>:
                    {html.escape(error.get('error', 'Unknown error'))}
                    <em>({error.get('type', 'Error')})</em>
                </div>
            </div>"""
            for error in errors
        ]

        warning_items = [
            f"""<div class="alert alert-warning">
                <span class="alert-icon">⚠️</span>
                <div>
                    <strong>{warning.get('plugin', 'Unknown')}</strong>:
                    {html.escape(warning.get('warning', 'Unknown warning'))}
                </div>
            </div>"""
            for warning in warnings
        ]

        return f"""
<div id="issues" class="section">
    <div class="section-header">
        <span class="section-icon">⚠️</span>
        <h2>Issues</h2>
    </div>

    {' '.join(error_items)}
    {' '.join(warning_items)}
</div>
"""

    def _format_summary_rows(self, results: Dict[str, Any]) -> str:
        """Format summary table rows."""
        rows = []

        for plugin_name, plugin_data in results.items():
            summary = plugin_data.get("summary", {})

            # Determine status
            if "errors" in plugin_data and plugin_data["errors"]:
                status = '<span style="color: #dc3545;">❌ Error</span>'
            else:
                status = '<span style="color: #28a745;">✅ Success</span>'

            # Get key findings
            findings = []
            for key, value in summary.items():
                if isinstance(value, (int, float)) and value > 0:
                    findings.append(f"{key.replace('_', ' ').title()}: {value}")
                elif isinstance(value, bool) and value:
                    findings.append(key.replace("_", " ").title())

            findings_str = ", ".join(findings[:3])  # Limit to 3 items
            if len(findings) > 3:
                findings_str += f" (+{len(findings) - 3} more)"

            rows.append(
                f"""
                <tr>
                    <td><strong>{plugin_name.replace('_', ' ').title()}</strong></td>
                    <td>{status}</td>
                    <td>{findings_str or 'No significant findings'}</td>
                </tr>
            """
            )

        return "\n".join(rows)

    def _format_footer(self) -> str:
        """Format footer section."""
        return """
<div class="footer">
    <p>Generated by <strong>DumpSleuth</strong> - Open Source Memory Dump Analysis Tool</p>
    <p><a href="https://github.com/yourusername/dumpsleuth" style="color: #667eea;">View on GitHub</a></p>
</div>
"""

    def _get_inline_scripts(self, data: Dict[str, Any]) -> str:
        """Get inline scripts with data."""
        return f"""
<script>
    const analysisData = {json.dumps(data, default=str)};

    // Add any additional interactive features here
    console.log('DumpSleuth Report Loaded', analysisData);
</script>
"""

    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, (int, float)):
            if isinstance(value, int) and value > 1000:
                return f"{value:,}"
            return str(value)
        elif isinstance(value, list):
            return f"{len(value)} items"
        elif isinstance(value, dict):
            return f"{len(value)} entries"
        else:
            return html.escape(str(value))

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def _get_plugin_icon(self, plugin_name: str) -> str:
        """Get icon for plugin."""
        icons = {
            "strings": "📝",
            "network": "🌐",
            "registry": "🗝️",
            "processes": "⚙️",
            "files": "📁",
            "memory": "💾",
        }

        return icons.get(plugin_name, "🔧")
