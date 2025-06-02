#!/usr/bin/env python3
"""
Process Information Extractor
Extract process-related information from dump files
"""

import re
import sys
import struct
from pathlib import Path
from typing import List, Dict, Any

def extract_process_info(file_path: str) -> Dict[str, Any]:
    """Extract process information from dump file"""
    info = {
        "process_name": "Unknown",
        "pid": "Unknown",
        "modules": [],
        "file_handles": [],
        "registry_keys": [],
        "network_info": [],
        "errors": []
    }
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
            
        # Convert to text for regex searches
        text = data.decode('utf-8', errors='ignore')
        
        # Extract process name from filename
        filename = Path(file_path).name
        if '.exe_' in filename:
            info["process_name"] = filename.split('.exe_')[0] + '.exe'
            
        # Look for loaded modules (DLLs)
        dll_pattern = r'([a-zA-Z0-9_]+\.dll)'
        dlls = list(set(re.findall(dll_pattern, text, re.IGNORECASE)))
        info["modules"] = dlls[:50]  # Limit to 50
        
        # Look for file paths
        file_pattern = r'[A-Za-z]:\\[^<>:"|?*\n\r\x00-\x1f]+'
        files = list(set(re.findall(file_pattern, text)))
        info["file_handles"] = files[:30]  # Limit to 30
        
        # Look for registry keys
        reg_pattern = r'HKEY_[A-Z_]+\\[^<>:"|?*\n\r\x00-\x1f]+'
        registry = list(set(re.findall(reg_pattern, text)))
        info["registry_keys"] = registry[:20]  # Limit to 20
        
        # Look for IP addresses
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = list(set(re.findall(ip_pattern, text)))
        info["network_info"] = ips[:10]  # Limit to 10
        
        # Look for error messages
        error_patterns = [
            r'error[^a-zA-Z][^.\n]{0,100}',
            r'exception[^a-zA-Z][^.\n]{0,100}',
            r'failed[^a-zA-Z][^.\n]{0,100}',
            r'access denied[^.\n]{0,100}',
        ]
        
        errors = []
        for pattern in error_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            errors.extend(matches)
            
        info["errors"] = list(set(errors))[:10]  # Limit to 10
        
    except Exception as e:
        info["extraction_error"] = str(e)
        
    return info

def format_process_info(info: Dict[str, Any]) -> str:
    """Format process information for display"""
    output = []
    output.append("PROCESS INFORMATION ANALYSIS")
    output.append("=" * 50)
    
    output.append(f"\nProcess Name: {info['process_name']}")
    output.append(f"Process ID: {info['pid']}")
    
    if info["modules"]:
        output.append(f"\nLoaded Modules ({len(info['modules'])} found):")
        for module in info["modules"][:20]:
            output.append(f"  • {module}")
        if len(info["modules"]) > 20:
            output.append(f"  ... and {len(info['modules']) - 20} more")
            
    if info["file_handles"]:
        output.append(f"\nFile Handles ({len(info['file_handles'])} found):")
        for file_path in info["file_handles"][:15]:
            output.append(f"  • {file_path}")
        if len(info["file_handles"]) > 15:
            output.append(f"  ... and {len(info['file_handles']) - 15} more")
            
    if info["registry_keys"]:
        output.append(f"\nRegistry Keys ({len(info['registry_keys'])} found):")
        for key in info["registry_keys"][:10]:
            output.append(f"  • {key}")
        if len(info["registry_keys"]) > 10:
            output.append(f"  ... and {len(info['registry_keys']) - 10} more")
            
    if info["network_info"]:
        output.append(f"\nNetwork Information ({len(info['network_info'])} found):")
        for ip in info["network_info"]:
            output.append(f"  • {ip}")
            
    if info["errors"]:
        output.append(f"\nError Messages ({len(info['errors'])} found):")
        for error in info["errors"][:5]:
            output.append(f"  • {error.strip()}")
        if len(info["errors"]) > 5:
            output.append(f"  ... and {len(info['errors']) - 5} more")
            
    if "extraction_error" in info:
        output.append(f"\nExtraction Error: {info['extraction_error']}")
        
    return "\n".join(output)

def main():
    if len(sys.argv) != 2:
        print("Usage: python process_info.py <dump_file>")
        sys.exit(1)
        
    dump_file = sys.argv[1]
    
    if not Path(dump_file).exists():
        print(f"ERROR: File not found: {dump_file}")
        sys.exit(1)
        
    print("Extracting process information...")
    info = extract_process_info(dump_file)
    
    output = format_process_info(info)
    print(output)
    
    # Save to file
    output_file = f"process_info_{Path(dump_file).stem}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
        
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main() 