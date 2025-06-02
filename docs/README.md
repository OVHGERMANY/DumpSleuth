# DumpSleuth Documentation

## Running the Tools

Basic usage:

```sh
# Automated analysis
python analyzer/dump_analyzer.py

# Manual analysis
python analyzer/manual_analysis.py

# String extraction
python analyzer/string_extractor.py
```

Reports are saved in the `reports/` directory.

## Project Structure

```
dumpsleuth/
├── analyzer/     # Core analysis scripts
├── docs/         # Documentation
├── reports/      # Analysis reports
├── scripts/      # Utility scripts
└── tools/        # Additional tools
```

## Requirements

- Python 3.7+
- Windows OS
- Sufficient disk space for dumps

## Setup

1. Install Python 3.7 or higher
2. Run `pip install -r scripts/requirements.txt`
3. Place your dump file in the project directory
4. Run the desired analysis tool

## Notes

- Always run analysis tools from the project root directory
- Keep original dump files backed up
- Check reports/ directory for analysis results 