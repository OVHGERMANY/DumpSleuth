#!/usr/bin/env python3
"""
Simple Hex Viewer Utility
Quick hex dump viewer for binary files
"""

import argparse
import sys
from pathlib import Path


def hex_dump(data, offset=0, width=16):
    """Generate hex dump output"""
    lines = []
    for i in range(0, len(data), width):
        chunk = data[i : i + width]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)

        # Pad hex part if needed
        hex_part = hex_part.ljust(width * 3 - 1)

        line = f"{offset + i:08X}  {hex_part}  |{ascii_part}|"
        lines.append(line)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Simple hex viewer for dump files")
    parser.add_argument("file", help="File to view")
    parser.add_argument("-o", "--offset", type=int, default=0, help="Start offset")
    parser.add_argument(
        "-l", "--length", type=int, default=512, help="Number of bytes to show"
    )
    parser.add_argument("-w", "--width", type=int, default=16, help="Bytes per line")

    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"ERROR: File not found: {args.file}")
        sys.exit(1)

    try:
        with open(args.file, "rb") as f:
            f.seek(args.offset)
            data = f.read(args.length)

        if not data:
            print("ERROR: No data at specified offset")
            sys.exit(1)

        print(f"File: {args.file}")
        print(f"Offset: 0x{args.offset:08X} ({args.offset})")
        print(f"Length: {len(data)} bytes")
        print("─" * 80)
        print(hex_dump(data, args.offset, args.width))

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
