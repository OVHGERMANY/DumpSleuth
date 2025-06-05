"""
Registry extractor plugin for DumpSleuth
"""

import re
from typing import Any, Dict, List

from ..core.plugin import AnalyzerPlugin, PluginMetadata


class RegistryExtractor(AnalyzerPlugin):
    """Extracts Windows Registry artifacts from memory dumps"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="registry_analyzer",
            version="1.0.0",
            author="DumpSleuth Team",
            description="Extracts Registry keys, values, and persistence mechanisms",
            tags=["registry", "windows", "persistence", "configuration"],
        )

    def analyze(self, data: bytes, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract registry-related information"""
        text = data.decode("utf-8", errors="ignore")

        results = {
            "registry_keys": self._extract_registry_keys(text),
            "run_keys": self._extract_run_keys(text),
            "services": self._extract_services(text),
            "file_associations": self._extract_file_associations(text),
            "installed_software": self._extract_installed_software(text),
            "persistence_mechanisms": self._find_persistence_mechanisms(text),
        }

        # Add statistics
        results["statistics"] = {
            "total_keys": len(results["registry_keys"]),
            "run_entries": len(results["run_keys"]),
            "services": len(results["services"]),
            "persistence_indicators": len(results["persistence_mechanisms"]),
        }

        return results

    def _extract_registry_keys(self, text: str) -> List[Dict[str, Any]]:
        """Extract registry key paths"""
        # Common registry hives
        hives = [
            r"HKEY_LOCAL_MACHINE",
            r"HKLM",
            r"HKEY_CURRENT_USER",
            r"HKCU",
            r"HKEY_CLASSES_ROOT",
            r"HKCR",
            r"HKEY_USERS",
            r"HKU",
            r"HKEY_CURRENT_CONFIG",
        ]

        keys = []
        pattern = r"(" + "|".join(hives) + r')\\[^<>:"|?*\n\r]{1,255}'

        for match in re.finditer(pattern, text, re.IGNORECASE):
            key_path = match.group()
            keys.append(
                {"path": key_path, "hive": match.group(1), "offset": match.start()}
            )

        return list({k["path"]: k for k in keys}.values())[:200]

    def _extract_run_keys(self, text: str) -> List[Dict[str, str]]:
        """Extract Run/RunOnce registry entries"""
        run_patterns = [
            r"Software\\Microsoft\\Windows\\CurrentVersion\\Run\\[^\\]+",
            r"Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\[^\\]+",
            r"Software\\Microsoft\\Windows\\CurrentVersion\\RunServices\\[^\\]+",
            r"Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Run\\[^\\]+",
        ]

        run_keys = []
        for pattern in run_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entry = match.group()
                # Try to extract the value
                value_match = re.search(
                    entry + r"\s*=\s*([^\r\n]+)",
                    text[match.start() : match.start() + 500],
                )
                value = value_match.group(1) if value_match else "Unknown"

                run_keys.append(
                    {
                        "key": entry,
                        "value": value,
                        "type": "startup",
                        "offset": match.start(),
                    }
                )

        return run_keys[:100]

    def _extract_services(self, text: str) -> List[Dict[str, str]]:
        """Extract Windows services from registry"""
        service_pattern = r"SYSTEM\\CurrentControlSet\\Services\\([^\\]+)"
        services = []

        for match in re.finditer(service_pattern, text, re.IGNORECASE):
            service_name = match.group(1)
            services.append(
                {"name": service_name, "path": match.group(), "offset": match.start()}
            )

        return list({s["name"]: s for s in services}.values())[:100]

    def _extract_file_associations(self, text: str) -> List[Dict[str, str]]:
        """Extract file associations"""
        assoc_pattern = r"\\\.([a-zA-Z0-9]+)\\Shell\\Open\\Command"
        associations = []

        for match in re.finditer(assoc_pattern, text, re.IGNORECASE):
            extension = match.group(1)
            associations.append(
                {
                    "extension": f".{extension}",
                    "key": match.group(),
                    "offset": match.start(),
                }
            )

        return associations[:50]

    def _extract_installed_software(self, text: str) -> List[Dict[str, str]]:
        """Extract installed software entries"""
        software_patterns = [
            r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\([^\\]+)",
            r"SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\([^\\]+)",
        ]

        software = []
        for pattern in software_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                app_name = match.group(1)
                software.append(
                    {"name": app_name, "path": match.group(), "offset": match.start()}
                )

        return list({s["name"]: s for s in software}.values())[:100]

    def _find_persistence_mechanisms(self, text: str) -> List[Dict[str, Any]]:
        """Find potential persistence mechanisms"""
        persistence = []

        # Known persistence locations
        persistence_keys = [
            # Startup locations
            r"CurrentVersion\\Run",
            r"CurrentVersion\\RunOnce",
            r"CurrentVersion\\RunServices",
            r"CurrentVersion\\Explorer\\Shell Folders\\Startup",
            # Services
            r"CurrentControlSet\\Services",
            # Scheduled tasks
            r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Schedule\\TaskCache",
            # Browser extensions
            r"SOFTWARE\\Google\\Chrome\\Extensions",
            r"SOFTWARE\\Mozilla\\Firefox\\Extensions",
            # AppInit DLLs
            r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Windows\\AppInit_DLLs",
            # Image File Execution Options
            r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options",
            # Winlogon
            r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon",
        ]

        for key in persistence_keys:
            pattern = re.compile(key, re.IGNORECASE)
            for match in pattern.finditer(text):
                # Get context around the match
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 200)
                context = text[start:end]

                persistence.append(
                    {
                        "type": self._categorize_persistence(key),
                        "location": key,
                        "context": context.strip(),
                        "offset": match.start(),
                        "risk_level": self._assess_risk_level(key, context),
                    }
                )

        return persistence[:50]

    def _categorize_persistence(self, key: str) -> str:
        """Categorize the type of persistence mechanism"""
        if "Run" in key:
            return "startup"
        elif "Services" in key:
            return "service"
        elif "Schedule" in key:
            return "scheduled_task"
        elif "Extensions" in key:
            return "browser_extension"
        elif "AppInit" in key:
            return "dll_injection"
        elif "Image File Execution" in key:
            return "debugger"
        elif "Winlogon" in key:
            return "winlogon"
        else:
            return "other"

    def _assess_risk_level(self, key: str, context: str) -> str:
        """Assess the risk level of a persistence mechanism"""
        high_risk_indicators = [
            "powershell",
            "cmd.exe",
            "wscript",
            "cscript",
            "regsvr32",
            "rundll32",
            "mshta",
            "bitsadmin",
        ]

        context_lower = context.lower()
        if any(indicator in context_lower for indicator in high_risk_indicators):
            return "high"
        elif "AppInit" in key or "Image File Execution" in key:
            return "high"
        elif "Run" in key:
            return "medium"
        else:
            return "low"

    def get_supported_formats(self) -> List[str]:
        return ["*"]  # Supports all formats

    def get_priority(self) -> int:
        return 15  # Higher priority for Windows systems
