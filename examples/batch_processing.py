"""
Batch Processing Example for DumpSleuth

This example shows how to analyze multiple dump files in parallel.
"""

from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, Any, List
from dumpsleuth import DumpAnalyzer
import logging
import time


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_single_dump(dump_path: Path, output_dir: Path) -> Dict[str, Any]:
    """Analyze a single dump file."""
    try:
        logger.info(f"Analyzing {dump_path.name}...")
        
        # Create analyzer
        analyzer = DumpAnalyzer(str(dump_path))
        
        # Run analysis
        results = analyzer.analyze()
        
        # Save results
        output_name = dump_path.stem + "_report"
        report_path = output_dir / f"{output_name}.html"
        results.save(str(report_path))
        
        # Get summary
        summary = analyzer.get_summary()
        
        return {
            'file': dump_path.name,
            'status': 'success',
            'report': str(report_path),
            'summary': summary
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze {dump_path}: {e}")
        return {
            'file': dump_path.name,
            'status': 'error',
            'error': str(e)
        }


def batch_analyze(dump_dir: Path, output_dir: Path, pattern: str = "*.dmp", max_workers: int = 4):
    """Analyze all dump files in a directory."""
    
    # Find all dump files
    dump_files = list(dump_dir.glob(pattern))
    logger.info(f"Found {len(dump_files)} dump files to analyze")
    
    if not dump_files:
        logger.warning("No dump files found!")
        return
        
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Track timing
    start_time = time.time()
    
    # Process dumps in parallel
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_dump = {
            executor.submit(analyze_single_dump, dump_file, output_dir): dump_file
            for dump_file in dump_files
        }
        
        # Process completed tasks
        for future in as_completed(future_to_dump):
            dump_file = future_to_dump[future]
            try:
                result = future.result()
                results.append(result)
                
                if result['status'] == 'success':
                    logger.info(f"✓ Completed: {result['file']}")
                else:
                    logger.error(f"✗ Failed: {result['file']} - {result.get('error', 'Unknown error')}")
                    
            except Exception as exc:
                logger.error(f"✗ Exception for {dump_file}: {exc}")
                results.append({
                    'file': dump_file.name,
                    'status': 'error',
                    'error': str(exc)
                })
    
    # Calculate statistics
    elapsed_time = time.time() - start_time
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'error')
    
    # Print summary
    print(f"\n{'='*60}")
    print("BATCH ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Total files processed: {len(dump_files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total time: {elapsed_time:.2f} seconds")
    print(f"Average time per file: {elapsed_time/len(dump_files):.2f} seconds")
    print(f"Output directory: {output_dir}")
    
    # Generate summary report
    generate_batch_summary(results, output_dir)


def generate_batch_summary(results: List[Dict], output_dir: Path):
    """Generate a summary report for batch analysis."""
    summary_path = output_dir / "batch_summary.html"
    
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Batch Analysis Summary</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        .success { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>Batch Analysis Summary</h1>
    <table>
        <tr>
            <th>File</th>
            <th>Status</th>
            <th>Details</th>
        </tr>
"""
    
    for result in results:
        status_class = result['status']
        status_symbol = "✓" if result['status'] == 'success' else "✗"
        
        details = ""
        if result['status'] == 'success':
            summary = result.get('summary', {})
            details = f"Report: <a href='{Path(result['report']).name}'>{Path(result['report']).name}</a>"
        else:
            details = f"Error: {result.get('error', 'Unknown')}"
            
        html_content += f"""
        <tr>
            <td>{result['file']}</td>
            <td class="{status_class}">{status_symbol} {result['status'].title()}</td>
            <td>{details}</td>
        </tr>
"""
    
    html_content += """
    </table>
</body>
</html>
"""
    
    with open(summary_path, 'w') as f:
        f.write(html_content)
        
    logger.info(f"Batch summary saved to: {summary_path}")


def main():
    # Configuration
    dump_directory = Path("path/to/dump/files")
    output_directory = Path("batch_reports")
    
    # Run batch analysis
    batch_analyze(
        dump_dir=dump_directory,
        output_dir=output_directory,
        pattern="*.dmp",  # Can also use "*.raw", "*.mem", etc.
        max_workers=4  # Number of parallel processes
    )


if __name__ == "__main__":
    main() 