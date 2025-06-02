#!/usr/bin/env python3
"""
Manual Analysis Tool
Interactive exploration of memory dump files
"""

import os
import sys
import struct
import binascii
from pathlib import Path
from typing import Optional, List, Tuple

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, IntPrompt
    from rich.text import Text
    import hexdump
except ImportError:
    print("Please install rich and hexdump: pip install rich hexdump")
    sys.exit(1)

class ManualAnalyzer:
    def __init__(self, dump_file: str):
        self.dump_file = dump_file
        self.console = Console()
        self.file_size = 0
        self.current_offset = 0
        self.bookmarks = {}
        
        if not Path(dump_file).exists():
            self.console.print(f"[red]❌ File not found: {dump_file}[/red]")
            sys.exit(1)
            
        self.file_size = Path(dump_file).stat().st_size
        self.console.print(f"[green]📁 Loaded: {dump_file} ({self.file_size:,} bytes)[/green]")
        
    def main_menu(self):
        """Display main menu and handle user input"""
        while True:
            self.console.print("\n" + "="*60)
            self.console.print("Manual Dump Analysis")
            self.console.print("="*60)
            
            menu_items = [
                "1. File Information",
                "2. Hex Viewer",
                "3. String Search",
                "4. Jump to Offset",
                "5. Bookmarks",
                "6. Data Analysis",
                "7. Export Data",
                "8. Help",
                "9. Exit"
            ]
            
            for item in menu_items:
                self.console.print(f"  {item}")
                
            choice = Prompt.ask("\nSelect option", choices=["1","2","3","4","5","6","7","8","9"])
            
            if choice == "1":
                self.show_file_info()
            elif choice == "2":
                self.hex_viewer()
            elif choice == "3":
                self.string_search()
            elif choice == "4":
                self.jump_to_offset()
            elif choice == "5":
                self.bookmarks_menu()
            elif choice == "6":
                self.data_analysis()
            elif choice == "7":
                self.export_menu()
            elif choice == "8":
                self.show_help()
            elif choice == "9":
                self.console.print("Goodbye!")
                break
                
    def show_file_info(self):
        """Display detailed file information"""
        file_path = Path(self.dump_file)
        stat = file_path.stat()
        
        table = Table(title="📊 File Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="yellow")
        
        table.add_row("Filename", file_path.name)
        table.add_row("Size", f"{self.file_size:,} bytes ({self.file_size / (1024*1024):.2f} MB)")
        table.add_row("Created", str(stat.st_ctime))
        table.add_row("Modified", str(stat.st_mtime))
        table.add_row("Current Offset", f"0x{self.current_offset:08X} ({self.current_offset:,})")
        
        # Try to identify file type by header
        with open(self.dump_file, 'rb') as f:
            header = f.read(16)
            
        table.add_row("Header (hex)", header.hex().upper())
        table.add_row("Header (ascii)", ''.join(chr(b) if 32 <= b <= 126 else '.' for b in header))
        
        # Possible file type
        file_type = "Unknown"
        if header.startswith(b'MDMP'):
            file_type = "Windows Minidump"
        elif header.startswith(b'PAGE'):
            file_type = "Windows Memory Dump"
        elif b'BEService' in header:
            file_type = "BattlEye Service Dump"
            
        table.add_row("Detected Type", file_type)
        
        self.console.print(table)
        
    def hex_viewer(self):
        """Interactive hex viewer"""
        bytes_per_page = 256
        
        while True:
            self.console.print(f"\n[bold cyan]🔍 Hex Viewer - Offset: 0x{self.current_offset:08X}[/bold cyan]")
            
            # Read data
            with open(self.dump_file, 'rb') as f:
                f.seek(self.current_offset)
                data = f.read(bytes_per_page)
                
            if not data:
                self.console.print("[red]❌ No data at this offset[/red]")
                return
                
            # Display hex dump
            self.console.print(Panel(hexdump.hexdump(data, result='return'), title="Hex Data"))
            
            # ASCII representation
            ascii_repr = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)
            self.console.print(f"[yellow]ASCII: {ascii_repr}[/yellow]")
            
            # Navigation options
            self.console.print("\n[bold]Navigation:[/bold]")
            self.console.print("  n/next - Next page")
            self.console.print("  p/prev - Previous page")
            self.console.print("  j/jump - Jump to offset")
            self.console.print("  s/search - Search for bytes")
            self.console.print("  b/bookmark - Add bookmark")
            self.console.print("  q/quit - Back to main menu")
            
            cmd = Prompt.ask("Command").lower()
            
            if cmd in ['n', 'next']:
                self.current_offset = min(self.current_offset + bytes_per_page, self.file_size - 1)
            elif cmd in ['p', 'prev']:
                self.current_offset = max(self.current_offset - bytes_per_page, 0)
            elif cmd in ['j', 'jump']:
                try:
                    offset_str = Prompt.ask("Enter offset (hex or decimal)")
                    if offset_str.startswith('0x'):
                        offset = int(offset_str, 16)
                    else:
                        offset = int(offset_str)
                    if 0 <= offset < self.file_size:
                        self.current_offset = offset
                    else:
                        self.console.print("[red]❌ Invalid offset[/red]")
                except ValueError:
                    self.console.print("[red]❌ Invalid offset format[/red]")
            elif cmd in ['s', 'search']:
                self.search_bytes()
            elif cmd in ['b', 'bookmark']:
                name = Prompt.ask("Bookmark name")
                self.bookmarks[name] = self.current_offset
                self.console.print(f"[green]✅ Bookmark '{name}' added at 0x{self.current_offset:08X}[/green]")
            elif cmd in ['q', 'quit']:
                break
                
    def search_bytes(self):
        """Search for byte patterns"""
        pattern_str = Prompt.ask("Enter search pattern (hex bytes, e.g., '41 42 43' or 'ABC')")
        
        try:
            # Try to parse as hex bytes first
            if ' ' in pattern_str:
                pattern = bytes.fromhex(pattern_str.replace(' ', ''))
            else:
                # Try as ASCII string
                try:
                    pattern = bytes.fromhex(pattern_str)
                except ValueError:
                    pattern = pattern_str.encode('ascii')
                    
            self.console.print(f"[cyan]🔍 Searching for pattern: {pattern.hex().upper()}[/cyan]")
            
            matches = []
            chunk_size = 1024 * 1024  # 1MB chunks
            
            with open(self.dump_file, 'rb') as f:
                offset = 0
                while offset < self.file_size:
                    f.seek(offset)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                        
                    pos = 0
                    while True:
                        found = chunk.find(pattern, pos)
                        if found == -1:
                            break
                        matches.append(offset + found)
                        pos = found + 1
                        
                        if len(matches) >= 100:  # Limit results
                            break
                            
                    offset += chunk_size - len(pattern) + 1
                    
                    if len(matches) >= 100:
                        break
                        
            if matches:
                self.console.print(f"[green]✅ Found {len(matches)} matches:[/green]")
                table = Table()
                table.add_column("Index", style="cyan")
                table.add_column("Offset (hex)", style="yellow")
                table.add_column("Offset (dec)", style="magenta")
                
                for i, match in enumerate(matches[:20]):  # Show first 20
                    table.add_row(str(i+1), f"0x{match:08X}", str(match))
                    
                self.console.print(table)
                
                if len(matches) > 20:
                    self.console.print(f"... and {len(matches) - 20} more matches")
                    
                # Option to jump to first match
                if Prompt.ask("Jump to first match?", choices=["y", "n"]) == "y":
                    self.current_offset = matches[0]
            else:
                self.console.print("[yellow]❌ Pattern not found[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]❌ Error: {e}[/red]")
            
    def string_search(self):
        """Search for ASCII strings"""
        search_term = Prompt.ask("Enter search term")
        min_length = IntPrompt.ask("Minimum string length", default=4)
        
        self.console.print(f"[cyan]🔤 Searching for strings containing '{search_term}'...[/cyan]")
        
        import re
        
        try:
            with open(self.dump_file, 'rb') as f:
                data = f.read()
                
            # Find ASCII strings
            pattern = re.compile(b'[\x20-\x7E]{' + str(min_length).encode() + b',}')
            strings = pattern.findall(data)
            
            matches = []
            for s in strings:
                try:
                    decoded = s.decode('ascii')
                    if search_term.lower() in decoded.lower():
                        # Find offset
                        offset = data.find(s)
                        matches.append((offset, decoded))
                except:
                    continue
                    
            if matches:
                self.console.print(f"[green]✅ Found {len(matches)} matching strings:[/green]")
                table = Table()
                table.add_column("Offset", style="cyan")
                table.add_column("String", style="yellow")
                
                for offset, string in matches[:20]:
                    table.add_row(f"0x{offset:08X}", string[:80] + ("..." if len(string) > 80 else ""))
                    
                self.console.print(table)
            else:
                self.console.print("[yellow]❌ No matching strings found[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]❌ Error: {e}[/red]")
            
    def jump_to_offset(self):
        """Jump to specific offset"""
        offset_str = Prompt.ask("Enter offset (hex with 0x prefix or decimal)")
        
        try:
            if offset_str.startswith('0x'):
                offset = int(offset_str, 16)
            else:
                offset = int(offset_str)
                
            if 0 <= offset < self.file_size:
                self.current_offset = offset
                self.console.print(f"[green]✅ Jumped to offset 0x{offset:08X}[/green]")
            else:
                self.console.print(f"[red]❌ Offset out of range (0 - 0x{self.file_size-1:08X})[/red]")
        except ValueError:
            self.console.print("[red]❌ Invalid offset format[/red]")
            
    def bookmarks_menu(self):
        """Manage bookmarks"""
        while True:
            self.console.print("\n[bold cyan]🔖 Bookmarks[/bold cyan]")
            
            if not self.bookmarks:
                self.console.print("[yellow]No bookmarks yet[/yellow]")
            else:
                table = Table()
                table.add_column("Name", style="cyan")
                table.add_column("Offset", style="yellow")
                
                for name, offset in self.bookmarks.items():
                    table.add_row(name, f"0x{offset:08X}")
                    
                self.console.print(table)
                
            self.console.print("\n1. Add bookmark")
            self.console.print("2. Jump to bookmark")
            self.console.print("3. Delete bookmark")
            self.console.print("4. Back to main menu")
            
            choice = Prompt.ask("Select option", choices=["1","2","3","4"])
            
            if choice == "1":
                name = Prompt.ask("Bookmark name")
                self.bookmarks[name] = self.current_offset
                self.console.print(f"[green]✅ Added bookmark '{name}' at 0x{self.current_offset:08X}[/green]")
            elif choice == "2":
                if self.bookmarks:
                    name = Prompt.ask("Bookmark name", choices=list(self.bookmarks.keys()))
                    self.current_offset = self.bookmarks[name]
                    self.console.print(f"[green]✅ Jumped to bookmark '{name}'[/green]")
            elif choice == "3":
                if self.bookmarks:
                    name = Prompt.ask("Bookmark to delete", choices=list(self.bookmarks.keys()))
                    del self.bookmarks[name]
                    self.console.print(f"[green]✅ Deleted bookmark '{name}'[/green]")
            elif choice == "4":
                break
                
    def data_analysis(self):
        """Analyze data at current position"""
        self.console.print(f"\n[bold cyan]🧪 Data Analysis at 0x{self.current_offset:08X}[/bold cyan]")
        
        with open(self.dump_file, 'rb') as f:
            f.seek(self.current_offset)
            data = f.read(64)  # Read 64 bytes for analysis
            
        if len(data) < 4:
            self.console.print("[red]❌ Not enough data[/red]")
            return
            
        table = Table(title="Data Interpretation")
        table.add_column("Type", style="cyan")
        table.add_column("Value", style="yellow")
        
        # Raw hex
        table.add_row("Raw Hex", data[:16].hex().upper())
        
        # ASCII
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[:16])
        table.add_row("ASCII", ascii_str)
        
        # Integer interpretations
        if len(data) >= 4:
            uint32_le = struct.unpack('<I', data[:4])[0]
            uint32_be = struct.unpack('>I', data[:4])[0]
            table.add_row("UINT32 (LE)", f"{uint32_le} (0x{uint32_le:08X})")
            table.add_row("UINT32 (BE)", f"{uint32_be} (0x{uint32_be:08X})")
            
        if len(data) >= 8:
            uint64_le = struct.unpack('<Q', data[:8])[0]
            table.add_row("UINT64 (LE)", f"{uint64_le} (0x{uint64_le:016X})")
            
        # Float interpretation
        if len(data) >= 4:
            try:
                float_val = struct.unpack('<f', data[:4])[0]
                table.add_row("Float (LE)", f"{float_val:.6f}")
            except:
                pass
                
        self.console.print(table)
        
        # Entropy analysis
        if len(data) >= 16:
            entropy = self.calculate_entropy(data[:16])
            self.console.print(f"\n[yellow]📊 Entropy: {entropy:.3f} (0=ordered, 8=random)[/yellow]")
            
    def calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy"""
        if len(data) == 0:
            return 0.0
            
        from collections import Counter
        import math
        
        counts = Counter(data)
        entropy = 0.0
        
        for count in counts.values():
            p = count / len(data)
            entropy -= p * math.log2(p)
            
        return entropy
        
    def export_menu(self):
        """Export data to file"""
        self.console.print("\n[bold cyan]📝 Export Data[/bold cyan]")
        self.console.print("1. Export current view (256 bytes)")
        self.console.print("2. Export range")
        self.console.print("3. Export all strings")
        self.console.print("4. Back to main menu")
        
        choice = Prompt.ask("Select option", choices=["1","2","3","4"])
        
        if choice == "1":
            self.export_current_view()
        elif choice == "2":
            self.export_range()
        elif choice == "3":
            self.export_strings()
        elif choice == "4":
            return
            
    def export_current_view(self):
        """Export current 256 bytes"""
        filename = Prompt.ask("Output filename", default="dump_export.bin")
        
        with open(self.dump_file, 'rb') as f:
            f.seek(self.current_offset)
            data = f.read(256)
            
        with open(filename, 'wb') as f:
            f.write(data)
            
        self.console.print(f"[green]✅ Exported {len(data)} bytes to {filename}[/green]")
        
    def export_range(self):
        """Export specific range"""
        start_str = Prompt.ask("Start offset (hex or decimal)")
        end_str = Prompt.ask("End offset (hex or decimal)")
        filename = Prompt.ask("Output filename", default="dump_range.bin")
        
        try:
            start = int(start_str, 16) if start_str.startswith('0x') else int(start_str)
            end = int(end_str, 16) if end_str.startswith('0x') else int(end_str)
            
            if start >= end or start < 0 or end > self.file_size:
                self.console.print("[red]❌ Invalid range[/red]")
                return
                
            with open(self.dump_file, 'rb') as f:
                f.seek(start)
                data = f.read(end - start)
                
            with open(filename, 'wb') as f:
                f.write(data)
                
            self.console.print(f"[green]✅ Exported {len(data)} bytes to {filename}[/green]")
            
        except ValueError:
            self.console.print("[red]❌ Invalid offset format[/red]")
            
    def export_strings(self):
        """Export all strings to text file"""
        filename = Prompt.ask("Output filename", default="dump_strings.txt")
        min_length = IntPrompt.ask("Minimum string length", default=4)
        
        import re
        
        with open(self.dump_file, 'rb') as f:
            data = f.read()
            
        pattern = re.compile(b'[\x20-\x7E]{' + str(min_length).encode() + b',}')
        strings = [s.decode('ascii') for s in pattern.findall(data)]
        
        with open(filename, 'w', encoding='utf-8') as f:
            for string in strings:
                f.write(string + '\n')
                
        self.console.print(f"[green]✅ Exported {len(strings)} strings to {filename}[/green]")
        
    def show_help(self):
        """Show help information"""
        help_text = """
[bold cyan]🎯 Manual Analysis Tool Help[/bold cyan]

[bold yellow]Navigation:[/bold yellow]
• Use the hex viewer to explore the dump byte by byte
• Jump to specific offsets using hex (0x1234) or decimal format
• Use bookmarks to mark interesting locations

[bold yellow]Search Features:[/bold yellow]
• Byte search: Find specific byte patterns (hex or ASCII)
• String search: Find readable text in the dump
• Pattern matching with regular expressions

[bold yellow]Data Analysis:[/bold yellow]
• Interpret data as different types (integers, floats, strings)
• Calculate entropy to detect encrypted/compressed data
• Export specific ranges for further analysis

[bold yellow]Tips:[/bold yellow]
• Look for ASCII strings that might reveal file paths, URLs, or error messages
• Check entropy - high entropy might indicate encrypted data
• Use bookmarks to mark interesting addresses
• Export suspicious areas for analysis with other tools

[bold yellow]Common Patterns in BEService dumps:[/bold yellow]
• BattlEye service configuration data
• Game process monitoring information
• Anti-cheat detection logs
• Network communication data
        """
        
        self.console.print(Panel(help_text, title="Help", border_style="cyan"))

def main():
    """Main function"""
    # Find dump files
    dump_files = list(Path('.').glob('*.dmp'))
    
    if not dump_files:
        print("❌ No .dmp files found in current directory!")
        sys.exit(1)
        
    if len(dump_files) == 1:
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
    
    # Start analyzer
    analyzer = ManualAnalyzer(dump_file)
    analyzer.main_menu()

if __name__ == "__main__":
    main() 