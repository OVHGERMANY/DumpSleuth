"""
Basic DumpSleuth Analysis Example

This example demonstrates how to perform a simple analysis on a memory dump file.
"""

from pathlib import Path
from dumpsleuth import DumpAnalyzer


def main():
    # Path to your dump file
    dump_file = "path/to/your/dump.dmp"
    
    # Create analyzer instance
    print(f"Analyzing {dump_file}...")
    analyzer = DumpAnalyzer(dump_file)
    
    # Run analysis
    results = analyzer.analyze()
    
    # Get summary
    summary = analyzer.get_summary()
    print("\nAnalysis Summary:")
    print(f"  Total processes found: {summary.get('processes_summary', {}).get('total_processes', 0)}")
    print(f"  Strings extracted: {summary.get('strings_summary', {}).get('total_strings', 0)}")
    print(f"  Network artifacts: {summary.get('network_summary', {}).get('total_artifacts', 0)}")
    print(f"  Registry keys: {summary.get('registry_summary', {}).get('total_keys', 0)}")
    
    # Save reports in multiple formats
    print("\nGenerating reports...")
    results.save("analysis_report.html")
    results.save("analysis_report.json")
    results.save("analysis_report.md")
    
    print("Analysis complete! Reports saved.")


if __name__ == "__main__":
    main() 