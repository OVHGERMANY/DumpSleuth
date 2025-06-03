"""
Process extractor plugin for DumpSleuth.

Extracts information about running processes from memory dumps.
"""

import logging
import re
import struct
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from ..core.parser import DumpData
from ..core.plugin import AnalyzerPlugin

logger = logging.getLogger(__name__)


class ProcessInfo:
    """Container for process information."""

    def __init__(self, pid: int = 0, name: str = "", parent_pid: int = 0):
        self.pid = pid
        self.name = name
        self.parent_pid = parent_pid
        self.command_line = ""
        self.threads = 0
        self.handles = 0
        self.modules = []
        self.memory_regions = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pid": self.pid,
            "name": self.name,
            "parent_pid": self.parent_pid,
            "command_line": self.command_line,
            "threads": self.threads,
            "handles": self.handles,
            "modules": self.modules,
            "memory_regions": len(self.memory_regions),
        }


class ProcessExtractorPlugin(AnalyzerPlugin):
    """Plugin for extracting process information from memory dumps."""

    def __init__(self):
        """Initialize the plugin."""
        super().__init__()
        self.config = {}

        # Process signatures for different platforms
        self.signatures = {
            "windows": {
                # EPROCESS signatures
                "eprocess_pool_tag": b"\x50\x72\x6f\x63",  # 'Proc'
                "peb_signature": b"\x00\x00\x00\x00\x00\x00\x00\x00",
            },
            "linux": {
                # task_struct patterns
                "comm_pattern": re.compile(rb"[\x20-\x7e]{1,15}\x00"),
            },
        }

    def get_name(self) -> str:
        """Get plugin name."""
        return "processes"

    def get_description(self) -> str:
        """Get plugin description."""
        return "Extracts running process information from memory dumps"

    def analyze(self, dump_data: DumpData) -> Dict[str, Any]:
        """
        Analyze dump for process information.

        Args:
            dump_data: Parsed dump data

        Returns:
            Dictionary containing process information
        """
        logger.info("Starting process extraction")

        processes = []
        errors = []

        try:
            # Detect OS type from dump metadata or content
            os_type = self._detect_os_type(dump_data)
            logger.info(f"Detected OS type: {os_type}")

            if os_type == "windows":
                processes = self._extract_windows_processes(dump_data)
            elif os_type == "linux":
                processes = self._extract_linux_processes(dump_data)
            else:
                # Generic extraction
                processes = self._extract_generic_processes(dump_data)

        except Exception as e:
            logger.error(f"Process extraction failed: {e}")
            errors.append(str(e))

        # Build process tree
        process_tree = self._build_process_tree(processes)

        # Generate summary
        summary = self._generate_summary(processes)

        return {
            "processes": [p.to_dict() for p in processes],
            "process_tree": process_tree,
            "summary": summary,
            "errors": errors,
        }

    def _detect_os_type(self, dump_data: DumpData) -> str:
        """Detect operating system type from dump."""
        # Check metadata first
        dump_format = dump_data.metadata.get("format", "")
        if "minidump" in dump_format or "dmp" in dump_format:
            return "windows"
        elif "elf" in dump_format:
            return "linux"

        # Check content patterns
        sample = dump_data.read(0, 1024 * 1024)  # First 1MB

        # Windows indicators
        if b"Windows" in sample or b"WINDOWS" in sample:
            return "windows"
        if b"ntoskrnl" in sample or b"NTOSKRNL" in sample:
            return "windows"

        # Linux indicators
        if b"Linux" in sample or b"linux" in sample:
            return "linux"
        if b"/proc/" in sample or b"/sys/" in sample:
            return "linux"

        return "unknown"

    def _extract_windows_processes(self, dump_data: DumpData) -> List[ProcessInfo]:
        """Extract processes from Windows dumps."""
        processes = []

        # Search for EPROCESS structures
        chunk_size = 1024 * 1024  # 1MB chunks
        offset = 0
        file_size = dump_data.metadata.get("file_size", 0)

        while offset < file_size:
            chunk = dump_data.read(offset, chunk_size)
            if not chunk:
                break

            # Search for process pool tags
            for i in range(0, len(chunk) - 4):
                if chunk[i : i + 4] == self.signatures["windows"]["eprocess_pool_tag"]:
                    # Potential EPROCESS structure
                    process = self._parse_eprocess(dump_data, offset + i)
                    if process:
                        processes.append(process)

            offset += chunk_size - 1024  # Overlap to catch boundaries

        # Also search for process names in strings
        name_pattern = re.compile(rb"([a-zA-Z0-9_\-]+\.exe)\x00")
        chunk = dump_data.read(0, min(10 * 1024 * 1024, file_size))  # First 10MB

        for match in name_pattern.finditer(chunk):
            name = match.group(1).decode("utf-8", errors="ignore")
            # Check if we already have this process
            if not any(p.name == name for p in processes):
                process = ProcessInfo(name=name)
                processes.append(process)

        return processes

    def _parse_eprocess(
        self, dump_data: DumpData, offset: int
    ) -> Optional[ProcessInfo]:
        """Parse EPROCESS structure (simplified)."""
        try:
            # This is a simplified parser - real EPROCESS parsing is complex
            data = dump_data.read(offset - 0x2E0, 0x500)  # Approximate offsets

            # Look for process name (ImageFileName)
            name_offset = 0x450  # Approximate offset
            name_bytes = data[name_offset : name_offset + 16]
            name_end = name_bytes.find(b"\x00")
            if name_end > 0:
                name = name_bytes[:name_end].decode("utf-8", errors="ignore")
                if name and name.isprintable():
                    process = ProcessInfo(name=name)

                    # Try to extract PID (simplified)
                    # Real parsing would need proper structure offsets
                    return process

        except Exception as e:
            logger.debug(f"Failed to parse EPROCESS at {offset}: {e}")

        return None

    def _extract_linux_processes(self, dump_data: DumpData) -> List[ProcessInfo]:
        """Extract processes from Linux dumps."""
        processes = []

        # Search for task_struct comm field (process names)
        chunk_size = 1024 * 1024
        offset = 0
        file_size = dump_data.metadata.get("file_size", 0)

        seen_names = set()

        while offset < file_size:
            chunk = dump_data.read(offset, chunk_size)
            if not chunk:
                break

            # Search for process names (comm field in task_struct)
            for match in self.signatures["linux"]["comm_pattern"].finditer(chunk):
                name = match.group(0).rstrip(b"\x00").decode("utf-8", errors="ignore")

                # Filter common false positives
                if (
                    name
                    and len(name) > 2
                    and name not in seen_names
                    and not name.startswith("/")
                    and "." not in name[-4:]
                ):  # Not a file extension

                    seen_names.add(name)
                    process = ProcessInfo(name=name)
                    processes.append(process)

            offset += chunk_size - 1024

        # Also look for command lines
        cmdline_pattern = re.compile(rb"/[a-zA-Z0-9_/\-]+(?:\s+[a-zA-Z0-9_\-=]+)*\x00")
        chunk = dump_data.read(0, min(10 * 1024 * 1024, file_size))

        for match in cmdline_pattern.finditer(chunk):
            cmdline = match.group(0).rstrip(b"\x00").decode("utf-8", errors="ignore")
            # Extract process name from command line
            parts = cmdline.split()
            if parts:
                name = parts[0].split("/")[-1]
                if name not in seen_names:
                    seen_names.add(name)
                    process = ProcessInfo(name=name)
                    process.command_line = cmdline
                    processes.append(process)

        return processes

    def _extract_generic_processes(self, dump_data: DumpData) -> List[ProcessInfo]:
        """Generic process extraction using common patterns."""
        processes = []
        seen_names = set()

        # Common executable patterns
        patterns = [
            re.compile(rb"([a-zA-Z0-9_\-]+\.exe)\x00"),  # Windows
            re.compile(rb"([a-zA-Z0-9_\-]+\.dll)\x00"),  # Windows DLLs
            re.compile(rb"/usr/bin/([a-zA-Z0-9_\-]+)\x00"),  # Linux
            re.compile(rb"/sbin/([a-zA-Z0-9_\-]+)\x00"),  # Linux
            re.compile(rb"com\.([a-zA-Z0-9_\-\.]+)"),  # Android/Java
        ]

        # Read first 10MB for process names
        chunk_size = min(10 * 1024 * 1024, dump_data.metadata.get("file_size", 0))
        chunk = dump_data.read(0, chunk_size)

        for pattern in patterns:
            for match in pattern.finditer(chunk):
                name = match.group(1).decode("utf-8", errors="ignore")
                if name and name not in seen_names:
                    seen_names.add(name)
                    process = ProcessInfo(name=name)
                    processes.append(process)

        return processes

    def _build_process_tree(self, processes: List[ProcessInfo]) -> Dict[str, Any]:
        """Build process tree from parent-child relationships."""
        tree = defaultdict(list)

        for process in processes:
            if process.parent_pid:
                tree[process.parent_pid].append(process.pid)

        return dict(tree)

    def _generate_summary(self, processes: List[ProcessInfo]) -> Dict[str, Any]:
        """Generate summary statistics."""
        if not processes:
            return {"total_processes": 0, "unique_names": 0, "common_processes": []}

        # Count occurrences
        name_counts = defaultdict(int)
        for process in processes:
            if process.name:
                name_counts[process.name] += 1

        # Find common processes
        common_processes = sorted(
            name_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            "total_processes": len(processes),
            "unique_names": len(name_counts),
            "common_processes": [
                {"name": name, "count": count} for name, count in common_processes
            ],
            "has_system_processes": any(
                "system" in p.name.lower()
                or "kernel" in p.name.lower()
                or "init" in p.name.lower()
                for p in processes
                if p.name
            ),
        }
