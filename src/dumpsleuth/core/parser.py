"""
Dump file parser module.

Handles reading and parsing various dump file formats with
support for large files using memory mapping.
"""

import os
import mmap
import struct
import logging
from pathlib import Path
from typing import Dict, Any, Optional, BinaryIO, Union
from dataclasses import dataclass
from contextlib import contextmanager

from .config import Config


logger = logging.getLogger(__name__)


@dataclass
class DumpData:
    """Container for parsed dump data."""
    file_path: Path
    file_handle: Optional[BinaryIO] = None
    mmap_handle: Optional[mmap.mmap] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
            
    @property
    def data(self) -> Union[bytes, mmap.mmap]:
        """Get the dump data (either mmap or bytes)."""
        return self.mmap_handle if self.mmap_handle else self.file_handle
        
    def read(self, offset: int = 0, size: int = -1) -> bytes:
        """Read data from dump."""
        if self.mmap_handle:
            if size == -1:
                return self.mmap_handle[offset:]
            return self.mmap_handle[offset:offset + size]
        elif self.file_handle:
            self.file_handle.seek(offset)
            return self.file_handle.read(size)
        else:
            raise RuntimeError("No data handle available")
            
    def close(self):
        """Close file handles."""
        if self.mmap_handle:
            self.mmap_handle.close()
        if self.file_handle:
            self.file_handle.close()


class DumpParser:
    """Parser for memory dump files."""
    
    # Common dump file signatures
    SIGNATURES = {
        b'MDMP': 'minidump',
        b'PAGEDU64': 'dmp64',
        b'PAGEDUMP': 'dmp32',
        b'HIBR': 'hibernation',
        b'EMF': 'vmware',
    }
    
    def __init__(self, dump_file: Union[str, Path], config: Config):
        """
        Initialize parser.
        
        Args:
            dump_file: Path to dump file
            config: Configuration object
        """
        self.dump_file = Path(dump_file)
        self.config = config
        self.file_size = self.dump_file.stat().st_size
        
        # Check file size limits
        max_size = self._parse_size(config.get('analysis.max_file_size', '2GB'))
        if self.file_size > max_size:
            raise ValueError(f"Dump file too large: {self.file_size:,} bytes "
                           f"(max: {max_size:,} bytes)")
                           
    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '500MB' to bytes."""
        size_str = size_str.upper().strip()
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024,
            'TB': 1024 * 1024 * 1024 * 1024
        }
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                number = float(size_str[:-len(suffix)])
                return int(number * multiplier)
                
        return int(size_str)  # Assume bytes if no suffix
        
    def detect_format(self, data: bytes) -> Optional[str]:
        """Detect dump file format from header."""
        for signature, format_name in self.SIGNATURES.items():
            if data.startswith(signature):
                return format_name
                
        # Check for ELF format (Linux core dumps)
        if data.startswith(b'\x7fELF'):
            return 'elf_core'
            
        # Check for Mach-O format (macOS)
        if data[:4] in (b'\xfe\xed\xfa\xce', b'\xce\xfa\xed\xfe',
                        b'\xfe\xed\xfa\xcf', b'\xcf\xfa\xed\xfe'):
            return 'macho_core'
            
        return None
        
    @contextmanager
    def _open_dump(self, recovery_mode: bool = False):
        """Context manager for opening dump file."""
        file_handle = None
        mmap_handle = None
        
        try:
            # Open file
            file_handle = open(self.dump_file, 'rb')
            
            # Use mmap for large files
            use_mmap = self.config.get('analysis.use_mmap', True)
            mmap_threshold = self._parse_size(
                self.config.get('analysis.mmap_threshold', '100MB')
            )
            
            if use_mmap and self.file_size > mmap_threshold:
                try:
                    mmap_handle = mmap.mmap(
                        file_handle.fileno(), 
                        0, 
                        access=mmap.ACCESS_READ
                    )
                    logger.info(f"Using memory-mapped file access")
                except Exception as e:
                    logger.warning(f"Failed to create mmap: {e}, using regular file access")
                    
            yield file_handle, mmap_handle
            
        except Exception as e:
            if not recovery_mode:
                raise
            logger.warning(f"Error opening dump file: {e}")
            yield None, None
        finally:
            if mmap_handle:
                mmap_handle.close()
            if file_handle:
                file_handle.close()
                
    def parse(self, recovery_mode: bool = False) -> DumpData:
        """
        Parse the dump file.
        
        Args:
            recovery_mode: Try to recover from errors
            
        Returns:
            DumpData object
        """
        logger.info(f"Parsing dump file: {self.dump_file}")
        
        with self._open_dump(recovery_mode) as (file_handle, mmap_handle):
            if not file_handle:
                raise IOError("Failed to open dump file")
                
            # Create dump data container
            dump_data = DumpData(
                file_path=self.dump_file,
                file_handle=file_handle,
                mmap_handle=mmap_handle
            )
            
            # Read header to detect format
            header = dump_data.read(0, 4096)
            dump_format = self.detect_format(header)
            
            if dump_format:
                logger.info(f"Detected dump format: {dump_format}")
                dump_data.metadata['format'] = dump_format
                
                # Parse format-specific metadata
                try:
                    self._parse_metadata(dump_data, dump_format)
                except Exception as e:
                    if not recovery_mode:
                        raise
                    logger.warning(f"Failed to parse metadata: {e}")
            else:
                logger.warning("Unknown dump format")
                dump_data.metadata['format'] = 'unknown'
                
            # Basic metadata
            dump_data.metadata['file_size'] = self.file_size
            dump_data.metadata['file_name'] = self.dump_file.name
            
            # Keep handles open for analysis
            # They will be closed when dump_data is garbage collected
            # or explicitly closed
            file_handle = None
            mmap_handle = None
            
            return dump_data
            
    def _parse_metadata(self, dump_data: DumpData, format: str):
        """Parse format-specific metadata."""
        if format == 'minidump':
            self._parse_minidump_header(dump_data)
        elif format in ('dmp64', 'dmp32'):
            self._parse_windows_dump_header(dump_data)
        elif format == 'elf_core':
            self._parse_elf_header(dump_data)
        # Add more format parsers as needed
            
    def _parse_minidump_header(self, dump_data: DumpData):
        """Parse Windows minidump header."""
        # MINIDUMP_HEADER structure
        header_data = dump_data.read(0, 32)
        if len(header_data) < 32:
            raise ValueError("Invalid minidump header")
            
        signature, version, stream_count, stream_rva, checksum, timestamp, flags = \
            struct.unpack('<4sIIIIII', header_data)
            
        dump_data.metadata.update({
            'signature': signature.decode('ascii', errors='ignore'),
            'version': version,
            'stream_count': stream_count,
            'timestamp': timestamp,
            'flags': flags
        })
        
    def _parse_windows_dump_header(self, dump_data: DumpData):
        """Parse Windows full dump header."""
        # Simplified parsing - would need full DUMP_HEADER structure
        header_data = dump_data.read(0, 4096)
        
        # Extract basic info
        dump_data.metadata['dump_type'] = 'windows_full'
        
        # Look for system info
        if b'Windows' in header_data:
            start = header_data.find(b'Windows')
            end = header_data.find(b'\x00', start)
            if end > start:
                dump_data.metadata['os_version'] = header_data[start:end].decode('utf-8', errors='ignore')
                
    def _parse_elf_header(self, dump_data: DumpData):
        """Parse ELF core dump header."""
        # ELF header structure
        header_data = dump_data.read(0, 64)
        if len(header_data) < 52:
            raise ValueError("Invalid ELF header")
            
        # Parse e_ident
        magic = header_data[:4]
        if magic != b'\x7fELF':
            raise ValueError("Invalid ELF magic")
            
        ei_class = header_data[4]  # 1=32-bit, 2=64-bit
        ei_data = header_data[5]   # 1=little-endian, 2=big-endian
        
        dump_data.metadata.update({
            'format_details': 'elf_core',
            'arch': '64-bit' if ei_class == 2 else '32-bit',
            'endianness': 'little' if ei_data == 1 else 'big'
        }) 