# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-01

### Added
- 🏗️ **Complete project restructure** with modular architecture
- 🔌 **Plugin-based architecture** for extensible analysis capabilities
- ⚙️ **Configuration management system** with YAML support
- 📊 **Multiple reporting formats**: HTML, JSON, and Markdown
- 🎨 **Rich CLI interface** with improved user experience
- 🧪 **Comprehensive testing framework** structure
- 📦 **Modern Python packaging** with pyproject.toml
- 🚀 **Performance optimizations** for large dump analysis

### Core Features
- **Modular extractors**: Strings, Network, Registry, Processes
- **Interactive HTML reports** with visual components
- **Plugin system** for custom analyzers
- **Progress indicators** with real-time feedback
- **Error handling** with graceful recovery modes
- **Memory-mapped file reading** for efficiency
- **Parallel processing** support for large dumps

### Project Organization
- Restructured into `src/dumpsleuth/` package layout
- Separated concerns: `core/`, `extractors/`, `reporting/`, `ui/`
- Organized tests into `unit/`, `integration/`, `fixtures/`
- Split requirements into `base.txt` and `dev.txt`
- Added comprehensive documentation structure

### Developer Experience
- Modern setup with `pyproject.toml` configuration
- Black code formatting configuration
- pytest with coverage reporting
- MyPy type checking configuration
- Clear entry points for CLI (`dumpsleuth` and `ds` commands)

### Breaking Changes
- 🚨 **Complete API redesign** - not backward compatible with v1.x
- New modular plugin architecture replaces monolithic design
- Configuration format changed to YAML
- Command-line interface significantly enhanced

### Migration Guide
- Old single-file approach replaced with modular plugin system
- Update any custom scripts to use new `DumpAnalyzer` API
- Configuration files need to be converted to YAML format
- CLI commands may have changed - run `dumpsleuth --help` for new options

## [1.0.0] - Previous Version
### Initial Features
- Basic memory dump analysis
- String extraction
- Simple reporting capabilities

---

**Legend**:
- 🏗️ Architecture
- 🔌 Plugins
- ⚙️ Configuration  
- 📊 Reporting
- 🎨 UI/UX
- 🧪 Testing
- 📦 Packaging
- 🚀 Performance
- �� Breaking Changes 