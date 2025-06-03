#!/usr/bin/env python3
"""
String Extractor Tool
Extract and analyze readable strings from memory dump files
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import track
    from rich.table import Table
except ImportError:
    print("Please install rich: pip install rich")
    sys.exit(1)


class StringExtractor:
    def __init__(self):
        self.console = Console()

    def extract_ascii_strings(self, data: bytes, min_length: int = 4) -> List[str]:
        """Extract ASCII strings from binary data"""
        pattern = re.compile(b"[\x20-\x7e]{" + str(min_length).encode() + b",}")
        return [s.decode("ascii") for s in pattern.findall(data)]

    def extract_unicode_strings(self, data: bytes, min_length: int = 4) -> List[str]:
        """Extract Unicode (UTF-16LE) strings from binary data"""
        pattern = re.compile(b"(?:[\x20-\x7e]\x00){" + str(min_length).encode() + b",}")
        strings = []
        for match in pattern.findall(data):
            try:
                decoded = match.decode("utf-16le").rstrip("\x00")
                if len(decoded) >= min_length:
                    strings.append(decoded)
            except:
                continue
        return strings

    def filter_strings(
        self, strings: List[str], filters: Dict[str, str]
    ) -> Dict[str, List[str]]:
        """Filter strings by categories"""
        categories = {
            "Network": [],
            "File Paths": [],
            "Registry": [],
            "Libraries": [],
            "Errors": [],
            "Process": [],
            "Security": [],
            "System": [],
            "Interesting": [],
        }

        patterns = {
            "Network": [
                r'https?://[^\s<>"\']+',
                r"[a-zA-Z0-9.-]+\.(com|net|org|io|gov|edu|mil)",
                r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
                r"api\.|www\.|ftp\.",
                r"tcp|udp|http|ssl|tls",
            ],
            "File Paths": [
                r'[A-Za-z]:\\[^<>:"|?*\n\r\x00-\x1f]+',
                r'\\\\[^\\]+\\[^<>:"|?*\n\r\x00-\x1f]+',
                r"\.[a-zA-Z0-9]{2,4}$",
                r"Program Files|Windows|System32|AppData",
            ],
            "Registry": [
                r'HKEY_[A-Z_]+\\[^<>:"|?*\n\r\x00-\x1f]+',
                r'SOFTWARE\\[^<>:"|?*\n\r\x00-\x1f]+',
                r'SYSTEM\\[^<>:"|?*\n\r\x00-\x1f]+',
                r"CurrentVersion|Run|Services",
            ],
            "Libraries": [
                r"\w+\.dll",
                r"\w+\.exe",
                r"\w+\.sys",
                r"kernel32|ntdll|user32|advapi32|ws2_32",
            ],
            "Errors": [
                r"error|failed|exception|crash|fault|violation",
                r"access denied|permission|unauthorized",
                r"not found|missing|corrupt|invalid",
                r"timeout|overflow|underflow",
            ],
            "Process": [
                r"process|thread|handle|mutex",
                r"pid|tid|session",
                r"running|stopped|suspended",
                r"priority|affinity",
            ],
            "Security": [
                r"crypto|encrypt|decrypt|hash|sha|md5",
                r"certificate|signature|verify|auth",
                r"security|protection|shield|guard",
                r"firewall|antivirus|defender",
            ],
            "System": [
                r"windows|microsoft|nt|win32",
                r"version|build|architecture|x64|x86",
                r"cpu|memory|thread|process|service",
                r"driver|device|hardware",
            ],
        }

        processed = set()

        for string in strings:
            if string in processed or len(string) < 4:
                continue

            processed.add(string)
            categorized = False
            string_lower = string.lower()

            for category, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if re.search(pattern, string_lower, re.IGNORECASE):
                        categories[category].append(string)
                        categorized = True
                        break
                if categorized:
                    break

            if not categorized and len(string) > 8 and any(c.isalpha() for c in string):
                categories["Interesting"].append(string)

        return categories

    def save_strings_to_file(self, strings: Dict[str, List[str]], output_file: str):
        """Save categorized strings to a file"""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Extracted Strings Analysis\n\n")

            for category, string_list in strings.items():
                if string_list:
                    f.write(f"## {category} ({len(string_list)} items)\n\n")
                    for string in string_list:
                        f.write(f"- {string}\n")
                    f.write("\n")

        self.console.print(f"[green]✅ Strings saved to: {output_file}[/green]")

    def display_results(self, categorized_strings: Dict[str, List[str]]):
        """Display categorized strings in a nice format"""
        total_strings = sum(len(strings) for strings in categorized_strings.values())

        self.console.print(f"\n[bold green]🎉 Analysis Complete![/bold green]")
        self.console.print(f"[cyan]📊 Total strings found: {total_strings}[/cyan]\n")

        for category, strings in categorized_strings.items():
            if not strings:
                continue

            table = Table(title=f"{category} ({len(strings)} items)")
            table.add_column("String", style="yellow", no_wrap=False)
            table.add_column("Length", style="cyan", justify="right")

            # Show top 20 strings for each category
            for string in strings[:20]:
                table.add_row(
                    string[:100] + ("..." if len(string) > 100 else ""),
                    str(len(string)),
                )

            if len(strings) > 20:
                table.add_row(f"... and {len(strings) - 20} more ...", "")

            self.console.print(table)
            self.console.print()

    def extract_from_file(
        self, file_path: str, min_length: int = 4, max_size_mb: int = 50
    ) -> Dict[str, List[str]]:
        """Extract strings from a file"""
        self.console.print(
            f"[bold cyan]🔍 Extracting strings from: {file_path}[/bold cyan]"
        )

        try:
            file_size = Path(file_path).stat().st_size

            if file_size > max_size_mb * 1024 * 1024:
                self.console.print(
                    f"[yellow]⚠️  Large file ({file_size // (1024*1024)}MB). Reading first {max_size_mb}MB only.[/yellow]"
                )

            with open(file_path, "rb") as f:
                data = f.read(max_size_mb * 1024 * 1024)

            self.console.print(f"[green]📖 Read {len(data):,} bytes[/green]")

            # Extract strings
            self.console.print("[cyan]🔤 Extracting ASCII strings...[/cyan]")
            ascii_strings = self.extract_ascii_strings(data, min_length)

            self.console.print("[cyan]🔤 Extracting Unicode strings...[/cyan]")
            unicode_strings = self.extract_unicode_strings(data, min_length)

            # Combine and deduplicate
            all_strings = list(set(ascii_strings + unicode_strings))
            self.console.print(
                f"[green]✅ Found {len(all_strings)} unique strings[/green]"
            )

            # Filter and categorize
            self.console.print("[cyan]🏷️  Categorizing strings...[/cyan]")
            categorized = self.filter_strings(all_strings, {})

            return categorized

        except Exception as e:
            self.console.print(f"[red]❌ Error processing file: {e}[/red]")
            return {}

    def search_strings(
        self, categorized_strings: Dict[str, List[str]], search_term: str
    ) -> List[str]:
        """Search for specific terms in extracted strings"""
        matches = []
        search_lower = search_term.lower()

        for category, strings in categorized_strings.items():
            for string in strings:
                if search_lower in string.lower():
                    matches.append(f"[{category}] {string}")

        return matches


def main():
    parser = argparse.ArgumentParser(
        description="Extract and analyze strings from dump files"
    )
    parser.add_argument("file", nargs="?", help="Dump file to analyze")
    parser.add_argument(
        "-l",
        "--min-length",
        type=int,
        default=4,
        help="Minimum string length (default: 4)",
    )
    parser.add_argument("-o", "--output", help="Output file for results")
    parser.add_argument("-s", "--search", help="Search for specific term in results")
    parser.add_argument(
        "--max-size",
        type=int,
        default=50,
        help="Maximum file size to read in MB (default: 50)",
    )

    args = parser.parse_args()

    extractor = StringExtractor()

    # Find dump file
    if args.file:
        dump_file = args.file
    else:
        dump_files = list(Path(".").glob("*.dmp"))
        if not dump_files:
            print(
                "❌ No .dmp files found! Specify a file or put a .dmp file in current directory."
            )
            sys.exit(1)
        elif len(dump_files) == 1:
            dump_file = str(dump_files[0])
        else:
            print("🔍 Multiple dump files found:")
            for i, file in enumerate(dump_files):
                print(f"  {i+1}. {file.name}")
            try:
                choice = int(input("\nSelect file number: ")) - 1
                dump_file = str(dump_files[choice])
            except (ValueError, IndexError):
                print("❌ Invalid selection!")
                sys.exit(1)

    if not Path(dump_file).exists():
        print(f"❌ File not found: {dump_file}")
        sys.exit(1)

    # Extract strings
    categorized_strings = extractor.extract_from_file(
        dump_file, args.min_length, args.max_size
    )

    if not categorized_strings:
        print("❌ No strings extracted!")
        sys.exit(1)

    # Search if requested
    if args.search:
        matches = extractor.search_strings(categorized_strings, args.search)
        extractor.console.print(
            f"\n[bold yellow]🔍 Search results for '{args.search}':[/bold yellow]"
        )
        for match in matches[:50]:  # Limit to 50 results
            extractor.console.print(f"  • {match}")
        if len(matches) > 50:
            extractor.console.print(f"  ... and {len(matches) - 50} more matches")
    else:
        # Display results
        extractor.display_results(categorized_strings)

    # Save to file if requested
    if args.output:
        extractor.save_strings_to_file(categorized_strings, args.output)
    else:
        # Auto-save with timestamp
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"strings_analysis_{timestamp}.md"
        extractor.save_strings_to_file(categorized_strings, output_file)


if __name__ == "__main__":
    main()
