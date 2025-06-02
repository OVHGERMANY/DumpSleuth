# DumpSleuth Examples

This directory contains example scripts demonstrating how to use DumpSleuth for various memory dump analysis tasks.

## Examples Overview

### 1. Basic Analysis (`basic_analysis.py`)
Demonstrates the simplest way to analyze a memory dump file.

**Features:**
- Load and analyze a dump file
- Extract strings, network artifacts, registry keys, and processes
- Generate reports in multiple formats (HTML, JSON, Markdown)
- Display analysis summary

**Usage:**
```python
python basic_analysis.py
```

### 2. Custom Plugin Development (`custom_plugin_example.py`)
Shows how to create your own plugin to extend DumpSleuth's capabilities.

**Features:**
- Create a custom email extractor plugin
- Register the plugin with the analyzer
- Extract email addresses from memory dumps
- Generate reports with custom findings

**Usage:**
```python
python custom_plugin_example.py
```

### 3. Batch Processing (`batch_processing.py`)
Demonstrates how to analyze multiple dump files efficiently using parallel processing.

**Features:**
- Scan directories for dump files
- Process multiple dumps in parallel
- Generate individual reports for each dump
- Create a summary report for all analyzed files
- Track success/failure statistics

**Usage:**
```python
python batch_processing.py
```

## Quick Start

1. **Install DumpSleuth:**
   ```bash
   pip install -e ..
   ```

2. **Update the dump file paths in the examples:**
   ```python
   dump_file = "path/to/your/dump.dmp"  # Change this to your actual dump file
   ```

3. **Run an example:**
   ```bash
   python examples/basic_analysis.py
   ```

## Sample Dumps

Place your memory dump files in the `sample_dumps/` directory. DumpSleuth supports various formats:
- Windows minidumps (`.dmp`, `.mdmp`)
- Windows full dumps (`.dmp`)
- Raw memory dumps (`.raw`, `.mem`, `.bin`)
- Virtual machine snapshots (`.vmem`, `.vmsn`)
- Linux core dumps

## Creating Your Own Examples

To create a new example:

1. Import DumpSleuth:
   ```python
   from dumpsleuth import DumpAnalyzer
   ```

2. Create an analyzer instance:
   ```python
   analyzer = DumpAnalyzer("path/to/dump.dmp")
   ```

3. Run analysis:
   ```python
   results = analyzer.analyze()
   ```

4. Save or process results:
   ```python
   results.save("report.html")
   ```

## Advanced Usage

### Custom Configuration
```python
from dumpsleuth import DumpAnalyzer, Config

config = Config()
config.analysis.string_min_length = 6
config.analysis.parallel_processing = True

analyzer = DumpAnalyzer("dump.dmp", config=config)
```

### Selective Plugin Usage
```python
analyzer = DumpAnalyzer("dump.dmp")

# Only use specific plugins
analyzer.plugin_manager.disable_all()
analyzer.plugin_manager.enable("strings")
analyzer.plugin_manager.enable("network")
```

### Progress Callbacks
```python
def on_progress(plugin_name, progress):
    print(f"{plugin_name}: {progress}%")

analyzer = DumpAnalyzer("dump.dmp")
analyzer.set_progress_callback(on_progress)
results = analyzer.analyze()
```

## Tips

1. **Large Dumps**: For dumps larger than 1GB, use memory-mapped file access (enabled by default)
2. **Performance**: Increase `max_workers` in config for faster parallel processing
3. **Memory Usage**: Set `analysis.chunk_size` to control memory usage during analysis
4. **Custom Patterns**: Add your own regex patterns to find specific data

## Troubleshooting

- **Out of Memory**: Reduce chunk size or disable parallel processing
- **Slow Analysis**: Enable parallel processing or reduce the number of enabled plugins
- **Missing Dependencies**: Run `pip install -r ../requirements/base.txt`

## Contributing

Have an interesting example? Please submit a pull request! Make sure to:
- Add clear documentation
- Include error handling
- Follow the existing code style
- Test with different dump formats 