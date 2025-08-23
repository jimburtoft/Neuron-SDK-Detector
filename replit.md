# Overview

✅ **COMPLETED**: AWS Neuron SDK Version Detection Tool is a fully functional Python CLI application that identifies and analyzes AWS Neuron SDK installations across different environments. The tool successfully:

- 🔍 **Detects System Packages**: Uses dpkg to find installed AWS Neuron system packages
- 🐍 **Scans Python Environments**: Identifies Neuron packages in current and virtual environments
- 📊 **Compares Package Versions**: Matches detected packages against comprehensive SDK database
- ⚠️ **Identifies Mixed Installations**: Detects when packages from multiple SDK versions are present
- ❌ **Highlights Unknown Versions**: Emphasizes package versions not found in any known SDK
- 📁 **Multi-Environment Support**: Scans virtual environments in `/opt` directory
- 🤖 **Simple & Verbose Modes**: Provides both quick version check and detailed package analysis

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
- Default: Simple version output
- `--verbose`: Detailed package information
- `--check-venvs`: Extended environment scanning
- `--update-db`: Database maintenance operations

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