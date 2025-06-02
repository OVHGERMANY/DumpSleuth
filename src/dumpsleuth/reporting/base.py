"""
Base reporter class for DumpSleuth reports.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Union


class Reporter(ABC):
    """Abstract base class for report generators."""
    
    def __init__(self):
        """Initialize reporter."""
        self.config = {}
        
    @abstractmethod
    def format_report(self, data: Dict[str, Any]) -> str:
        """
        Format the analysis data into a report.
        
        Args:
            data: Analysis results dictionary
            
        Returns:
            Formatted report as string
        """
        pass
        
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for this report format."""
        pass
        
    def save(self, data: Dict[str, Any], filepath: Union[str, Path]):
        """
        Save report to file.
        
        Args:
            data: Analysis results dictionary
            filepath: Path to save the report
        """
        filepath = Path(filepath)
        
        # Add extension if not present
        if not filepath.suffix:
            filepath = filepath.with_suffix(self.get_file_extension())
            
        # Format report
        report_content = self.format_report(data)
        
        # Write to file
        mode = 'w' if isinstance(report_content, str) else 'wb'
        with open(filepath, mode) as f:
            f.write(report_content)
            
    def set_config(self, config: Dict[str, Any]):
        """Set reporter configuration."""
        self.config = config 