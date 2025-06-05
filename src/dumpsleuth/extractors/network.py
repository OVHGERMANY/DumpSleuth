"""
Network extractor plugin for DumpSleuth
"""

import re
from typing import Any, Dict, List

from ..core.plugin import AnalyzerPlugin, PluginMetadata


class NetworkExtractor(AnalyzerPlugin):
    """Analyzes network-related artifacts in memory dumps"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="network_analyzer",
            version="1.0.0",
            author="DumpSleuth Team",
            description="Extracts network connections, URLs, and IP addresses",
            tags=["network", "urls", "connections", "ip"],
        )

    def analyze(self, data: bytes, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract network-related information"""
        # Convert to string for regex (ignore errors)
        text = data.decode("utf-8", errors="ignore")

        results = {
            "urls": self._extract_urls(text),
            "ip_addresses": self._extract_ips(text),
            "email_addresses": self._extract_emails(text),
            "domains": self._extract_domains(text),
            "network_shares": self._extract_network_shares(text),
            "ports": self._extract_ports(text),
        }

        # Add statistics
        results["statistics"] = {
            "total_urls": len(results["urls"]),
            "total_ips": len(results["ip_addresses"]),
            "total_emails": len(results["email_addresses"]),
            "total_domains": len(results["domains"]),
            "unique_ports": len(results["ports"]),
        }

        return results

    def _extract_urls(self, text: str) -> List[Dict[str, Any]]:
        """Extract URLs with context"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = []

        for match in re.finditer(url_pattern, text):
            url = match.group()
            # Get surrounding context (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()

            urls.append({"url": url, "context": context, "offset": match.start()})

        return urls[:100]  # Limit to 100 results

    def _extract_ips(self, text: str) -> List[Dict[str, str]]:
        """Extract IP addresses"""
        ip_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
        ips = []

        for match in re.finditer(ip_pattern, text):
            ip = match.group()
            # Basic validation
            if all(0 <= int(octet) <= 255 for octet in ip.split(".")):
                ips.append(
                    {"ip": ip, "type": self._classify_ip(ip), "offset": match.start()}
                )

        return list({ip["ip"]: ip for ip in ips}.values())[:100]

    def _classify_ip(self, ip: str) -> str:
        """Classify IP address type"""
        octets = [int(x) for x in ip.split(".")]

        if octets[0] == 10:
            return "private_class_a"
        elif octets[0] == 172 and 16 <= octets[1] <= 31:
            return "private_class_b"
        elif octets[0] == 192 and octets[1] == 168:
            return "private_class_c"
        elif octets[0] == 127:
            return "loopback"
        elif octets[0] >= 224:
            return "multicast"
        else:
            return "public"

    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses"""
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        emails = list(set(re.findall(email_pattern, text)))
        return emails[:50]  # Limit results

    def _extract_domains(self, text: str) -> List[Dict[str, str]]:
        """Extract domain names"""
        domain_pattern = r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b"
        domains = []

        for match in re.finditer(domain_pattern, text):
            domain = match.group().lower()
            # Filter out common false positives
            if not any(
                domain.endswith(ext) for ext in [".dll", ".exe", ".sys", ".dat"]
            ):
                domains.append(
                    {
                        "domain": domain,
                        "tld": domain.split(".")[-1],
                        "offset": match.start(),
                    }
                )

        return list({d["domain"]: d for d in domains}.values())[:100]

    def _extract_network_shares(self, text: str) -> List[str]:
        """Extract network share paths"""
        share_pattern = r"\\\\[a-zA-Z0-9\-\.]+\\[a-zA-Z0-9\$\-_\.]+"
        shares = list(set(re.findall(share_pattern, text)))
        return shares[:50]

    def _extract_ports(self, text: str) -> List[int]:
        """Extract port numbers"""
        port_pattern = r"(?:port|Port|PORT)[:\s]*(\d{1,5})"
        ports = []

        for match in re.finditer(port_pattern, text):
            port = int(match.group(1))
            if 1 <= port <= 65535:
                ports.append(port)

        return sorted(list(set(ports)))

    def get_supported_formats(self) -> List[str]:
        return ["*"]  # Supports all formats

    def get_priority(self) -> int:
        return 10  # Medium priority
