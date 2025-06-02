# Dumps Directory

This directory is dedicated to storing memory dump files for analysis with DumpSleuth.

## Directory Structure

```
dumps/
├── README.md         # This file
├── .gitkeep         # Ensures directory is tracked by git
├── temp/            # Temporary processing directory
│   └── .gitkeep
└── [your dump files here]
```

## Usage

### Placing Dump Files

Simply copy or move your dump files into this directory:

```bash
# Copy a dump file
cp /path/to/memory.dmp dumps/

# Move multiple dump files
mv *.dmp dumps/
```

### Supported Formats

DumpSleuth automatically detects the following dump file extensions:
- `.dmp` - Windows memory dumps
- `.dump` - Generic dump files
- `.mdmp` - Minidump files
- `.hdmp` - Full heap dumps
- `.core` - Linux/Unix core dumps

### Analyzing Dumps

Once dump files are in this directory, you can analyze them using:

```bash
# Analyze all dumps in the directory
dumpsleuth analyze-all

# Analyze a specific dump
dumpsleuth analyze dumps/memory.dmp

# List available dumps
dumpsleuth list-dumps
```

### Temporary Files

The `temp/` subdirectory is used for:
- Intermediate processing files
- Extracted data during analysis
- Temporary caches

This directory is automatically cleaned up after analysis completes.

### Global Access

The dumps directory can be accessed from anywhere in your code using:

```python
from dumpsleuth.core.paths import get_dumps_dir, list_dump_files

# Get the dumps directory path
dumps_path = get_dumps_dir()

# List all dump files
dump_files = list_dump_files()

# List specific dump files
windows_dumps = list_dump_files("*.dmp")
```

## Important Notes

1. **Git Ignored**: All dump files in this directory are ignored by git to prevent accidentally committing large binary files.

2. **Storage**: Dump files can be very large. Ensure you have sufficient disk space.

3. **Security**: Memory dumps may contain sensitive information. Handle them appropriately and delete them when no longer needed.

4. **Organization**: Consider creating subdirectories for different projects or dates:
   ```
   dumps/
   ├── 2024-01-15/
   ├── project-a/
   └── incident-reports/
   ```

## Cleaning Up

To remove all dump files while preserving the directory structure:

```bash
# Remove all dump files (keeps .gitkeep and README.md)
find dumps/ -type f -name "*.dmp" -o -name "*.dump" -o -name "*.mdmp" -o -name "*.hdmp" -o -name "*.core" | xargs rm -f

# Or use Python
python -c "from dumpsleuth.core.paths import get_dump_paths; get_dump_paths().clean_temp()"
``` 