#!/usr/bin/env python3
"""
Memory Dump Analysis Tool
Automated analysis for dump files
"""

import os
import re
import sys
import datetime
from pathlib import Path
from typing import List, Dict, Any

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import track
    from rich.text import Text
    from rich.markdown import Markdown
    import hexdump
    import magic
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Please run: pip install -r scripts/requirements.txt")
    sys.exit(1)

# Import common module
if __name__ == "__main__":
    import common
else:
    from . import common

class DumpAnalyzer:
    def __init__(self, dump_file: str):
        self.dump_file = dump_file
        self.console = common.get_console()
        self.results = {}
        self.analysis_dir = Path("analysis_results")
        self.analysis_dir.mkdir(exist_ok=True)
        
    def banner(self):
        """Display banner"""
        common.print_banner(self.console)
        
    def basic_file_info(self) -> Dict[str, Any]:
        """Get basic information about the dump file"""
        self.console.print("\n>> Basic File Information")
        
        file_path = Path(self.dump_file)
        if not file_path.exists():
            self.console.print(f"ERROR: File not found: {self.dump_file}")
            return {}
            
        # File stats
        stat = file_path.stat()
        file_info = {
            "filename": file_path.name,
            "size": stat.st_size,
            "size_human": common.format_size(stat.st_size),
            "created": datetime.datetime.fromtimestamp(stat.st_ctime),
            "modified": datetime.datetime.fromtimestamp(stat.st_mtime),
        }
        
        # Try to get file type
        try:
            file_info["file_type"] = magic.from_file(str(file_path))
        except:
            file_info["file_type"] = "Unknown"
            
        # Parse filename for info
        filename_parts = file_path.stem.split('_')
        if len(filename_parts) >= 3:
            file_info["process_name"] = filename_parts[0]
            file_info["crash_date"] = filename_parts[1] if len(filename_parts) > 1 else "Unknown"
            file_info["crash_time"] = filename_parts[2] if len(filename_parts) > 2 else "Unknown"
            
        # Display results
        table = Table(title="File Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in file_info.items():
            table.add_row(key.replace('_', ' ').title(), str(value))
            
        self.console.print(table)
        return file_info
        
    def extract_strings(self, min_length: int = 4, max_strings: int = 1000) -> Dict[str, Any]:
        """Extract readable strings from the dump file"""
        self.console.print(f"\n[bold yellow]>> Extracting Strings (min length: {min_length})[/bold yellow]")
        
        try:
            with open(self.dump_file, 'rb') as f:
                data = f.read()
                
            string_data = common.extract_strings(data, min_length)
            strings = string_data["all"][:max_strings]
            
        except Exception as e:
            self.console.print(f"[red]Error extracting strings: {e}[/red]")
            return {"raw_strings": [], "categorized": {}, "total_count": 0}
            
        # Categorize strings
        categorized = self.categorize_strings(strings)
        
        # Display summary
        self.console.print(f"[green]>> Found {len(strings)} unique strings[/green]")
        
        for category, items in categorized.items():
            if items:
                self.console.print(f"\n[bold]{category} ({len(items)} items):[/bold]")
                for item in items[:10]:  # Show first 10
                    self.console.print(f"  • {item}")
                if len(items) > 10:
                    self.console.print(f"  ... and {len(items) - 10} more")
        
        return {
            "raw_strings": strings,
            "categorized": categorized,
            "total_count": len(strings)
        }
        
    def categorize_strings(self, strings: List[str]) -> Dict[str, List[str]]:
        """Categorize strings into different types"""
        categories = {
            "URLs/Domains": [],
            "File Paths": [],
            "Registry Keys": [],
            "DLL Names": [],
            "Error Messages": [],
            "Network Related": [],
            "Security Related": [],
            "System Info": [],
            "Other Interesting": []
        }
        
        patterns = {
            "URLs/Domains": [
                r'https?://[^\s]+',
                r'[a-zA-Z0-9.-]+\.(com|net|org|io|gov|edu|mil)',
                r'api\.',
                r'www\.',
                r'ftp\.',
            ],
            "File Paths": [
                r'[A-Za-z]:\\[^<>:"|?*\n\r]*',
                r'/[a-zA-Z0-9/_.-]+',
                r'\.exe|\.dll|\.sys|\.log|\.txt|\.dmp',
            ],
            "Registry Keys": [
                r'HKEY_[A-Z_]+\\[^<>:"|?*\n\r]*',
                r'SOFTWARE\\[^<>:"|?*\n\r]*',
                r'SYSTEM\\[^<>:"|?*\n\r]*',
            ],
            "DLL Names": [
                r'\w+\.dll',
                r'kernel32|ntdll|user32|advapi32',
            ],
            "Error Messages": [
                r'error|failed|exception|crash|fault',
                r'access denied|permission|invalid',
                r'not found|missing|corrupt',
                r'violation|overflow|underflow',
            ],
            "Network Related": [
                r'tcp|udp|http|ssl|tls|socket',
                r'port|connection|network',
                r'server|client|host',
            ],
            "Security Related": [
                r'crypto|encrypt|decrypt|hash',
                r'certificate|signature|verify',
                r'security|protection|authentication',
            ],
            "System Info": [
                r'windows|microsoft|nt',
                r'version|build|architecture',
                r'cpu|memory|thread|process',
            ],
        }
        
        for string in strings:
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
                    
            if not categorized and len(string) > 10:
                categories["Other Interesting"].append(string)
                
        return categories
        
    def analyze_memory_structure(self) -> Dict[str, Any]:
        """Analyze the memory dump structure"""
        self.console.print(f"\n[bold yellow]>> Memory Structure Analysis[/bold yellow]")
        
        try:
            with open(self.dump_file, 'rb') as f:
                # Read first 1KB to analyze header
                header = f.read(1024)
                
            analysis = {
                "file_size": os.path.getsize(self.dump_file),
                "magic_bytes": header[:16].hex(),
                "possible_format": self.identify_dump_format(header),
                "entropy": common.calculate_entropy(header),
                "null_bytes": header.count(b'\x00'),
                "printable_chars": sum(1 for b in header if 32 <= b <= 126),
            }
            
            # Display results
            table = Table(title="Memory Structure")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="magenta")
            
            for key, value in analysis.items():
                table.add_row(key.replace('_', ' ').title(), str(value))
                
            self.console.print(table)
            return analysis
            
        except Exception as e:
            self.console.print(f"[red]Error analyzing memory structure: {e}[/red]")
            return {}
            
    def identify_dump_format(self, header: bytes) -> str:
        """Try to identify the dump file format"""
        # Common dump file signatures
        signatures = {
            b'MDMP': 'Windows Minidump',
            b'PAGE': 'Windows Memory Dump',
            b'DMP\x00': 'Windows Crash Dump',
            b'HIBR': 'Windows Hibernation File',
        }
        
        for sig, format_name in signatures.items():
            if sig in header[:100]:
                return format_name
                
        return "Unknown/Custom Format"
        
    def search_for_patterns(self) -> Dict[str, List[str]]:
        """Search for interesting patterns in the dump"""
        self.console.print(f"\n[bold yellow]>> Pattern Recognition[/bold yellow]")
        
        results = {}
        
        try:
            with open(self.dump_file, 'rb') as f:
                # Read in chunks to handle large files
                chunk_size = 1024 * 1024  # 1MB chunks
                data = b''
                
                while chunk := f.read(chunk_size):
                    data += chunk
                    if len(data) > 10 * 1024 * 1024:  # Limit to 10MB for analysis
                        break
                        
                # Convert to string for regex (ignore errors)
                text = data.decode('utf-8', errors='ignore')
                
                for pattern_name, pattern in common.PATTERNS.items():
                    matches = list(set(re.findall(pattern, text, re.IGNORECASE)))
                    results[pattern_name] = matches[:50]  # Limit results
                    
                    if matches:
                        self.console.print(f"\n[bold green]{pattern_name}:[/bold green]")
                        for match in matches[:10]:
                            self.console.print(f"  • {match}")
                        if len(matches) > 10:
                            self.console.print(f"  ... and {len(matches) - 10} more")
                            
        except Exception as e:
            self.console.print(f"[red]Error searching patterns: {e}[/red]")
            
        return results
        
    def generate_report(self):
        """Generate a comprehensive analysis report"""
        self.console.print(f"\n[bold yellow]>> Generating Report[/bold yellow]")
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.analysis_dir / f"analysis_report_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Memory Dump Analysis Report\n\n")
            f.write(f"**File**: {self.dump_file}\n")
            f.write(f"**Analysis Date**: {datetime.datetime.now()}\n\n")
            f.write(f"---\n\n")
            
            # Write all collected results with better formatting
            for section, data in self.results.items():
                f.write(f"## {section}\n\n")
                
                if section == "Extracted Strings" and isinstance(data, dict):
                    # Special handling for the new string extraction format
                    f.write(f"**Total Strings Found**: {data.get('total_count', 0)}\n\n")
                    
                    # Write categorized strings
                    if 'categorized' in data:
                        f.write(f"### Categorized Strings\n\n")
                        for category, items in data['categorized'].items():
                            if items:
                                f.write(f"#### {category} ({len(items)} items)\n\n")
                                for item in items:  # Show all items in report
                                    f.write(f"- `{item}`\n")
                                f.write("\n")
                    
                elif isinstance(data, dict):
                    # Handle other dictionaries
                    if section == "Pattern Matches":
                        for pattern_type, matches in data.items():
                            if matches:
                                f.write(f"### {pattern_type} ({len(matches)} found)\n\n")
                                for match in matches:
                                    f.write(f"- `{match}`\n")
                                f.write("\n")
                    else:
                        # Regular dictionary formatting
                        for key, value in data.items():
                            f.write(f"- **{key.replace('_', ' ').title()}**: {value}\n")
                        
                elif isinstance(data, list):
                    # Handle lists
                    for item in data:
                        f.write(f"- {item}\n")
                        
                f.write("\n---\n\n")
                
        self.console.print(f"[green]>> Report saved to: {report_file}[/green]")
        
    def run_analysis(self):
        """Run the complete analysis"""
        self.banner()
        
        self.console.print(f"[bold green]>> Analyzing: {self.dump_file}[/bold green]\n")
        
        # Run all analysis steps
        self.results["File Information"] = self.basic_file_info()
        self.results["Memory Structure"] = self.analyze_memory_structure()
        self.results["Extracted Strings"] = self.extract_strings()
        self.results["Pattern Matches"] = self.search_for_patterns()
        
        # Generate final report
        self.generate_report()
        
        # Final summary
        self.console.print("\n" + "="*60)
        self.console.print("[bold green]>> Analysis Complete![/bold green]")
        self.console.print(f">> Results saved in: {self.analysis_dir}")
        self.console.print(">> Check the generated report for detailed findings!")
        self.console.print("="*60)

def main():
    """Main function"""
    dump_file = common.select_dump_file()
    
    if not dump_file:
        sys.exit(1)
    
    # Run analysis
    analyzer = DumpAnalyzer(dump_file)
    analyzer.run_analysis()

if __name__ == "__main__":
    main() 