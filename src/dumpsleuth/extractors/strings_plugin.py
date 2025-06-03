"""
String extractor plugin for DumpSleuth
"""

import re
from typing import Any, Dict, List, Set

from ..core.plugin import AnalyzerPlugin, PluginMetadata


class StringExtractor(AnalyzerPlugin):
    """Extracts and categorizes readable strings from memory dumps"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="string_extractor",
            version="2.0.0",
            author="DumpSleuth Team",
            description="Extracts ASCII and Unicode strings with intelligent categorization",
            tags=["strings", "text", "unicode", "ascii", "patterns"],
        )

    def analyze(self, data: bytes, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and analyze strings from the dump data"""
        config = context.get("config", {})
        min_length = config.get("string_min_length", 4)

        # Extract strings
        ascii_strings = self._extract_ascii_strings(data, min_length)
        unicode_strings = self._extract_unicode_strings(data, min_length)

        # Combine and deduplicate
        all_strings = list(set(ascii_strings + unicode_strings))

        # Categorize strings
        categorized = self._categorize_strings(all_strings)

        # Find interesting patterns
        patterns = self._find_patterns(all_strings)

        # Calculate statistics
        stats = self._calculate_statistics(categorized, patterns)

        return {
            "total_strings": len(all_strings),
            "categorized": categorized,
            "patterns": patterns,
            "statistics": stats,
            "encoding_distribution": {
                "ascii": len(ascii_strings),
                "unicode": len(unicode_strings),
            },
        }

    def _extract_ascii_strings(self, data: bytes, min_length: int) -> List[str]:
        """Extract ASCII strings from binary data"""
        pattern = rb"[\x20-\x7E]{" + str(min_length).encode() + rb",}"
        return [s.decode("ascii", errors="ignore") for s in re.findall(pattern, data)]

    def _extract_unicode_strings(self, data: bytes, min_length: int) -> List[str]:
        """Extract Unicode (UTF-16LE) strings from binary data"""
        pattern = rb"(?:[\x20-\x7E]\x00){" + str(min_length).encode() + rb",}"
        strings = []

        for match in re.findall(pattern, data):
            try:
                decoded = match.decode("utf-16le", errors="ignore").rstrip("\x00")
                if len(decoded) >= min_length:
                    strings.append(decoded)
            except:
                continue

        return strings

    def _categorize_strings(self, strings: List[str]) -> Dict[str, List[str]]:
        """Categorize strings by type"""
        categories = {
            "urls": [],
            "file_paths": [],
            "registry_keys": [],
            "dll_names": [],
            "error_messages": [],
            "network_related": [],
            "security_related": [],
            "system_info": [],
            "commands": [],
            "credentials": [],
            "interesting": [],
        }

        # Pattern definitions
        patterns = {
            "urls": [
                r'https?://[^\s<>"\']+',
                r'ftp://[^\s<>"\']+',
                r"[a-zA-Z0-9.-]+\.(com|net|org|io|gov|edu|mil|co\.[a-z]{2})",
            ],
            "file_paths": [
                r'[A-Za-z]:\\[^<>:"|?*\n\r]+',
                r'\\\\[^\\]+\\[^<>:"|?*\n\r]+',
                r"/[a-zA-Z0-9/_.-]+\.[a-zA-Z0-9]+",
                r'%[A-Z]+%\\[^<>:"|?*\n\r]+',
            ],
            "registry_keys": [
                r'HKEY_[A-Z_]+\\[^<>:"|?*\n\r]+',
                r'SOFTWARE\\[^<>:"|?*\n\r]+',
                r'SYSTEM\\[^<>:"|?*\n\r]+',
            ],
            "dll_names": [r"\w+\.dll", r"\w+\.exe", r"\w+\.sys", r"\w+\.ocx"],
            "error_messages": [
                r".*error.*|.*failed.*|.*exception.*",
                r".*access denied.*|.*permission.*",
                r".*not found.*|.*missing.*|.*invalid.*",
            ],
            "commands": [
                r"powershell.*|cmd.*|wmic.*",
                r"net\s+(use|user|share|view)",
                r"reg\s+(add|delete|query)",
                r"schtasks.*|at\s+\d+",
            ],
            "credentials": [
                r"password[:\s=]+\S+",
                r"pwd[:\s=]+\S+",
                r"user(name)?[:\s=]+\S+",
                r"api[_-]?key[:\s=]+\S+",
            ],
        }

        processed = set()

        for string in strings:
            if string in processed or len(string) < 4:
                continue

            processed.add(string)
            categorized = False

            # Check each category
            for category, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if re.search(pattern, string, re.IGNORECASE):
                        categories[category].append(string)
                        categorized = True
                        break
                if categorized:
                    break

            # If not categorized but interesting
            if not categorized and len(string) > 10:
                # Check for interesting characteristics
                if self._is_interesting(string):
                    categories["interesting"].append(string)

        # Limit results per category
        for category in categories:
            categories[category] = categories[category][:200]

        return categories

    def _is_interesting(self, string: str) -> bool:
        """Determine if a string is interesting based on various heuristics"""
        # Check for high entropy (possible encoded/encrypted data)
        if self._calculate_entropy(string) > 4.5:
            return True

        # Check for base64 patterns
        if re.match(r"^[A-Za-z0-9+/]{20,}={0,2}$", string):
            return True

        # Check for hex strings
        if re.match(r"^[0-9A-Fa-f]{16,}$", string):
            return True

        # Check for potential API keys or tokens
        if re.search(r"[A-Za-z0-9]{32,}", string):
            return True

        return False

    def _calculate_entropy(self, string: str) -> float:
        """Calculate Shannon entropy of a string"""
        import math
        from collections import Counter

        if not string:
            return 0.0

        counter = Counter(string)
        length = len(string)
        entropy = 0.0

        for count in counter.values():
            probability = count / length
            entropy -= probability * math.log2(probability)

        return entropy

    def _find_patterns(self, strings: List[str]) -> Dict[str, List[str]]:
        """Find specific patterns that might be of interest"""
        patterns_found = {
            "ip_addresses": [],
            "email_addresses": [],
            "bitcoin_addresses": [],
            "credit_cards": [],
            "phone_numbers": [],
            "hashes": {"md5": [], "sha1": [], "sha256": []},
        }

        # IP addresses
        ip_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"

        # Email addresses
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

        # Bitcoin addresses
        bitcoin_pattern = r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"

        # Credit card patterns (simplified)
        cc_pattern = r"\b(?:\d[ -]*?){13,19}\b"

        # Phone numbers
        phone_pattern = r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"

        # Hash patterns
        hash_patterns = {
            "md5": r"\b[a-fA-F0-9]{32}\b",
            "sha1": r"\b[a-fA-F0-9]{40}\b",
            "sha256": r"\b[a-fA-F0-9]{64}\b",
        }

        for string in strings:
            # Check each pattern
            for match in re.findall(ip_pattern, string):
                if self._is_valid_ip(match):
                    patterns_found["ip_addresses"].append(match)

            patterns_found["email_addresses"].extend(re.findall(email_pattern, string))
            patterns_found["bitcoin_addresses"].extend(
                re.findall(bitcoin_pattern, string)
            )

            # Credit cards (with basic Luhn check)
            for match in re.findall(cc_pattern, string):
                digits = re.sub(r"\D", "", match)
                if len(digits) >= 13 and len(digits) <= 19:
                    patterns_found["credit_cards"].append(match)

            patterns_found["phone_numbers"].extend(re.findall(phone_pattern, string))

            # Hashes
            for hash_type, pattern in hash_patterns.items():
                patterns_found["hashes"][hash_type].extend(re.findall(pattern, string))

        # Deduplicate
        for key in patterns_found:
            if key == "hashes":
                for hash_type in patterns_found["hashes"]:
                    patterns_found["hashes"][hash_type] = list(
                        set(patterns_found["hashes"][hash_type])
                    )[:50]
            else:
                patterns_found[key] = list(set(patterns_found[key]))[:50]

        return patterns_found

    def _is_valid_ip(self, ip: str) -> bool:
        """Check if an IP address is valid"""
        try:
            parts = ip.split(".")
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False

    def _calculate_statistics(
        self, categorized: Dict[str, List[str]], patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate statistics about the extracted strings"""
        total_categorized = sum(len(items) for items in categorized.values())

        # Find most common strings
        all_strings = []
        for items in categorized.values():
            all_strings.extend(items)

        from collections import Counter

        string_counts = Counter(all_strings)
        most_common = string_counts.most_common(20)

        return {
            "total_categorized": total_categorized,
            "categories_breakdown": {
                category: len(items) for category, items in categorized.items()
            },
            "patterns_found": {
                "ip_addresses": len(patterns.get("ip_addresses", [])),
                "email_addresses": len(patterns.get("email_addresses", [])),
                "potential_credentials": len(categorized.get("credentials", [])),
                "urls": len(categorized.get("urls", [])),
                "commands": len(categorized.get("commands", [])),
            },
            "most_common_strings": [
                {"string": string[:100], "count": count}
                for string, count in most_common
            ],
        }

    def get_supported_formats(self) -> List[str]:
        return ["*"]  # Supports all formats

    def get_priority(self) -> int:
        return 20  # High priority - strings are fundamental
