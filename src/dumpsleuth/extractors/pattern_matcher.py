"""Pattern matching plugin for DumpSleuth."""

import re
from typing import Dict, Any, List

from ..core.plugin import AnalyzerPlugin, PluginMetadata


class PatternMatcher(AnalyzerPlugin):
    """Search memory dumps for common patterns like URLs, IPs and secrets."""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="pattern_matcher",
            version="1.0.0",
            author="DumpSleuth Team",
            description="Searches dump data for common regex based patterns",
            tags=["patterns", "regex", "search"],
        )

    def analyze(self, data: bytes, context: Dict[str, Any]) -> Dict[str, Any]:
        """Match configured patterns in the given dump data."""
        text = data.decode("utf-8", errors="ignore")
        config = context.get("config", {})
        pattern_cfg = config.get("analysis", {}).get("patterns", {})
        includes = set(pattern_cfg.get("include", []))

        regexes: Dict[str, str] = {
            "urls": r"https?://[^\s<>\"'`]+",
            "ip_addresses": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
            "email_addresses": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            "file_paths": r"[A-Za-z]:\\\\[^<>:\"|?*\n\r]+|/[\w./-]+",
            "registry_keys": r"HKEY_[A-Z_]+\\\\[^<>:\"|?*\n\r]+",
            "passwords": r"password\s*=\s*\S+",
            "crypto_keys": r"-----BEGIN (?:RSA|DSA|EC|PGP) PRIVATE KEY-----",
        }

        matches: Dict[str, List[str]] = {}
        for name, regex in regexes.items():
            if includes and name not in includes:
                continue
            found = re.findall(regex, text, re.IGNORECASE)
            matches[name] = list(dict.fromkeys(found))[:50]

        summary = {key: len(values) for key, values in matches.items()}
        return {"matches": matches, "summary": summary}

    def get_supported_formats(self) -> List[str]:
        return ["*"]

    def get_priority(self) -> int:
        return 15
