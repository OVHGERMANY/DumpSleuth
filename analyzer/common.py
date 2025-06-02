#!/usr/bin/env python3
"""
Common utilities for dump analysis tools
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Union
from rich.console import Console

# Common patterns for analysis
PATTERNS = {
    "ip_addresses": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "urls": r'https?://[^\s<>"]+',
    "registry": r'HKEY_[A-Z_]+\\[^\x00-\x1f\x7f-\xff]*',
    "file_ext": r'\.\w{2,4}\b',
    "hex_values": r'0x[a-fA-F0-9]{4,}',
    "version": r'\d+\.\d+\.\d+(?:\.\d+)?',
}

def get_console() -> Console:
    """Get a shared console instance"""
    return Console()

def print_banner(console: Console = None) -> None:
    """Print the standard banner"""
    if not console:
        console = get_console()
    banner = """
================================================================
                     DUMP SLEUTH
                Memory Dump Analysis
================================================================
    """
    console.print(banner, style="bold")

def extract_strings(data: bytes, min_length: int = 4) -> Dict[str, List[str]]:
    """Extract ASCII and Unicode strings from binary data"""
    # ASCII strings
    ascii_pattern = re.compile(b'[\x20-\x7E]{' + str(min_length).encode() + b',}')
    ascii_strings = [s.decode('ascii') for s in ascii_pattern.findall(data)]
    
    # Unicode strings
    unicode_pattern = re.compile(b'(?:[\x20-\x7E]\x00){' + str(min_length).encode() + b',}')
    unicode_strings = []
    for match in unicode_pattern.findall(data):
        try:
            decoded = match.decode('utf-16le').rstrip('\x00')
            if len(decoded) >= min_length:
                unicode_strings.append(decoded)
        except:
            continue
    
    return {
        "ascii": ascii_strings,
        "unicode": unicode_strings,
        "all": list(set(ascii_strings + unicode_strings))
    }

def calculate_entropy(data: bytes) -> float:
    """Calculate Shannon entropy of data"""
    if len(data) == 0:
        return 0.0
        
    import math
    from collections import Counter
    
    counts = Counter(data)
    entropy = 0.0
    
    for count in counts.values():
        p = count / len(data)
        entropy -= p * math.log2(p)
        
    return entropy

def format_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def find_dump_files(directory: Union[str, Path] = ".") -> List[Path]:
    """Find all .dmp files in directory"""
    path = Path(directory)
    return list(path.glob('*.dmp'))

def select_dump_file() -> str:
    """Interactively select a dump file"""
    dump_files = find_dump_files()
    
    if not dump_files:
        print("ERROR: No .dmp files found in current directory!")
        print("TIP: Make sure your dump file is in the same folder as this script.")
        return None
        
    if len(dump_files) == 1:
        return str(dump_files[0])
    else:
        print(">> Multiple dump files found:")
        for i, file in enumerate(dump_files):
            print(f"  {i+1}. {file.name}")
        
        try:
            choice = int(input("\nSelect file number: ")) - 1
            return str(dump_files[choice])
        except (ValueError, IndexError):
            print("ERROR: Invalid selection!")
            return None 