# DumpSleuth

Memory dump analysis doesn't have to be complicated. DumpSleuth is a straightforward toolkit that helps you understand what's inside memory dump files, with tools for analysis, pattern matching, and detailed reporting.

## What's Inside

- Memory dump analyzer with hex viewer
- Smart pattern detection
- String finder and analyzer
- Report generator
- Windows batch scripts to make your life easier

## Getting Started

1. Grab the latest release
2. Run `scripts/quick_start.bat`
3. Pick what you want to do:
   - Run the analyzer
   - Dig through the dump manually
   - Pull out interesting strings
   - Set up your environment

## What You'll Need

- Windows machine
- Python 3.7 or newer
- About 500MB free space
- Admin rights (for some features)

## Project Layout
```
dumpsleuth/
├── analyzer/     # Main analysis tools
├── docs/        # Guides & docs
├── reports/     # Where reports go
├── scripts/     # Helper scripts
└── tools/       # Extra utilities
```

## Documentation

Check out these guides to get started:
- [Setup Guide](docs/SETUP_GUIDE.md)
- [Example Analysis](docs/EXAMPLE_OUTPUT.md)
- [Environment Setup](docs/VIRTUAL_ENV_GUIDE.md)
- [WinDbg Reference](docs/WINDBG_COMMANDS.md)

## License

This project is distributed under a personal-use license. In short:
- No sharing or redistributing
- No commercial use
- No modifications
- No incorporating into other projects

See [LICENSE](LICENSE) for the full terms. Questions about licensing? Email
james.nelson@jamesnelsonsec.xyz

## Important Note

This is for educational purposes only. Make sure you:
- Have permission to analyze any dumps
- Follow the rules and laws in your area
- Use the tools responsibly

I'm not responsible for any misuse or unauthorized use of this software. 