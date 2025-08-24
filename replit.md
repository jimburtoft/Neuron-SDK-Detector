# Overview

✅ **COMPLETED**: AWS Neuron SDK Version Detection Tool is a fully functional Python CLI application that identifies and analyzes AWS Neuron SDK installations across different environments. The tool successfully:

- 🔍 **Detects System Packages**: Uses apt/dpkg/rpm to find installed AWS Neuron system packages
- 🐍 **Scans Python Environments**: Identifies Neuron packages in current and virtual environments
- 📊 **Compares Package Versions**: Matches detected packages against comprehensive SDK database with 37+ versions
- ⚠️ **Identifies Mixed Installations**: Detects when packages from multiple SDK versions are present
- ❌ **Highlights Unknown Versions**: Emphasizes package versions not found in any known SDK with closest version suggestions
- 📁 **Multi-Environment Support**: Scans virtual environments in `/opt` directory with selective targeting
- 🤖 **Multiple Output Modes**: Simple, verbose, script-friendly, and information modes
- 📅 **Release Date Tracking**: Shows SDK release dates for temporal context
- 🎯 **Visual Indicators**: Emphasis characters for out-of-date and unknown packages
- 🔧 **Script Integration**: Machine-readable output for automation and CI/CD pipelines
- 📈 **Database Management**: Auto-updating version database with GitHub integration

The tool addresses the complexity of AWS Neuron SDK's multi-package architecture where different components may have different version numbers within the same SDK release.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Components

The application follows a two-script architecture with clear separation of functionality:

**Standalone Detection Script (`neuron_detector.py`)**
- Single-file architecture containing all detection functionality
- Integrated package detection for system and Python environments  
- Built-in version database management with GitHub download capability
- Command-line interface with simple and verbose output modes
- Downloads `neuron_versions.json` from GitHub if not found locally
- Caches database locally for future use

**Database Updater Script (`neuron_database_updater.py`)**
- Dedicated scraping and database maintenance functionality
- Scrapes AWS Neuron documentation for package version information
- Extracts data from current and historical release pages
- Uses trafilatura for content extraction and requests for HTTP handling
- Builds comprehensive JSON database with all SDK versions
- Independent operation - can update database without affecting detection

## Data Flow Architecture

1. **Detection Phase**: Package detector scans system and Python environments
2. **Database Loading**: Version database loads from local file or downloads from remote source
3. **Analysis Phase**: Detected packages are matched against known SDK releases
4. **Output Generation**: Results formatted based on verbosity settings

## Error Handling Strategy

- Graceful degradation when database is unavailable
- Fallback to local files when remote resources fail
- Mixed installation detection for inconsistent environments
- Unknown version warnings for unrecognized packages

## Command-Line Interface Design

Simple default behavior with progressive disclosure through optional flags:
- **Default**: Simple version output with release dates
- **`--verbose`**: Detailed package information and SDK breakdowns
- **`--check-venvs [VENV_NAME]`**: Extended environment scanning with optional single environment targeting
- **`--version`**: Script-friendly version output (exits with error on mixed installations)
- **`--info [--verbose]`**: Latest SDK information and update instructions, optionally with full version history
- **`--debug`**: Comprehensive package detection troubleshooting
- **`--data-file PATH`**: Custom version database file location

## Latest Features (Added)

### Enhanced Output Features
- **Closest Version Detection**: Unknown packages show nearest known versions above and below
- **Visual Emphasis**: ⚠️ for out-of-date packages, ❌ for unknown packages
- **Release Date Integration**: All SDK versions display with their release dates
- **Individual Environment Logic**: Each virtual environment assessed independently for mixed installations

### Script Integration Features
- **Version Flag**: Machine-readable SDK version output for automation
- **Error Handling**: Proper exit codes for script integration (0=success, 1=error/mixed)
- **Selective Environment Scanning**: Target specific virtual environments by name

### Information and Maintenance
- **Info Mode**: Display latest SDK version, database stats, and update instructions
- **Comprehensive Version History**: Chronological listing of all known SDK versions with dates
- **Database Auto-Download**: Automatic retrieval from GitHub with local caching

# External Dependencies

## Third-Party Python Libraries

**trafilatura** - Web content extraction library for parsing AWS documentation pages with intelligent content detection and cleanup.

**requests** - HTTP client library for downloading version database and scraping documentation with session management and timeout handling.

## System Dependencies

**dpkg** - Debian package management system used for detecting installed system packages on Ubuntu/Debian systems.

**subprocess** - Python standard library for executing system commands and parsing dpkg output.

## External Data Sources

**AWS Neuron Documentation** - Primary source for package version information, scraped from:
- Current release page: `awsdocs-neuron.readthedocs-hosted.com/en/latest/release-notes/releasecontent.html`
- Previous releases page: `awsdocs-neuron.readthedocs-hosted.com/en/latest/release-notes/prev/content.html`

**GitHub Repository** - Default location for version database JSON file hosting at `raw.githubusercontent.com/jimburtoft/Neuron-What-Am-I/main/neuron_versions.json`.

## Environment Dependencies

**Virtual Environment Support** - Scans Python virtual environments in `/opt` directory structure commonly used in AWS EC2 instances and DLAMI installations.

**Ubuntu/Debian Systems** - Primary target platform using apt/dpkg package management, specifically tested on Ubuntu 22 LTS systems.