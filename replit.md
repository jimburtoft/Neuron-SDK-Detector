# AWS Neuron SDK Management Suite

## Overview

The AWS Neuron SDK Management Suite is a comprehensive Python CLI toolset designed to detect, analyze, and update AWS Neuron SDK packages across system and virtual environments. The project addresses the complexity of managing the AWS Neuron SDK, which consists of multiple system and Python packages with different versioning schemes across various SDK releases.

The suite provides two main tools:
1. **Detection Tool** (`neuron_detector.py`) - Identifies installed Neuron packages and matches them to SDK releases
2. **Pre-built Update Scripts** (`update_to_sdk_*.sh`) - Ready-to-use shell scripts for upgrading to specific SDK versions
3. **Database Management** (`neuron_database_updater.py`) - Scrapes AWS documentation to maintain version databases

## Recent Changes

**November 1, 2025:**
- Added SDK 2.26.1 to version database (39 total SDK versions now)
- Removed Python update script generator (neuron_update.py) - replaced with pre-built shell scripts
- Project now provides ready-to-use update shell scripts (update_to_sdk_2_23_0.sh through update_to_sdk_2_26_1.sh)
- Added --support flag to neuron_detector.py for copy-paste friendly output to support tickets
  - Includes product name (from DMI), system packages (apt/yum), and Python packages (pip)
  - Output matches format of commands support teams request
- Fixed pip upgrade logic in all update scripts - now only upgrades installed packages (doesn't install new ones)
- Added aws-neuronx-runtime-discovery to Python packages section in all update scripts
- Verified shared component detection: packages that exist in both 2.26.0 and 2.26.1 (like aws-neuronx-runtime-discovery==2.9) won't trigger false mixed installation warnings when anchor package (neuronx-cc) points to 2.26.1

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Components

**Package Detection Engine**
- Multi-source package detection supporting both system packages (apt/dpkg/rpm) and Python packages (pip)
- Virtual environment scanning with selective targeting in `/opt` directory
- Anchor-based detection using neuronx-cc/neuron-cc versions as authoritative SDK indicators
- Mixed installation detection to identify packages from multiple SDK versions

**Version Database System**
- JSON-based package version database (`neuron_versions.json`) containing 37+ SDK versions
- Auto-download mechanism from GitHub when database is not found locally
- Documentation scraping system using trafilatura for extracting package versions from AWS Neuron documentation
- Local caching for offline use

**Pre-built Update Scripts**
- Ready-to-use shell scripts for SDK versions 2.23.0 through 2.26.1
- Only upgrades packages that are already installed (safe updates)
- Uses apt --only-upgrade for system packages and pip existence checks for Python packages
- Version wildcard handling for repository version suffixes
- Held package detection and management
- Optional fresh installation mode (commented sections)

**CLI Interface**
- Multiple output modes: simple, verbose, script-friendly, information, and support modes
- Support ticket output (--support flag): Copy-paste friendly format for support teams
- Visual indicators for out-of-date and unknown packages

### Data Architecture

**Package Classification**
- System packages: Neuron packages installed via system package managers
- Python packages: Neuron packages installed via pip in various environments
- Known package prefixes for both system and Python package detection

**Version Matching Algorithm**
- SDK version detection based on installed package versions
- Closest version detection for unknown packages
- Mixed installation analysis across multiple SDK versions

**Database Schema**
- Hierarchical structure: SDK version → Platform (Inf1/Inf2/Trn1) → Package → Version
- Release date tracking for chronological analysis
- Platform-specific package version mapping

### Testing Framework

**Comprehensive Test Suite**
- Functional tests based on real-world AWS Neuron system examples
- Package detection regression tests
- Update script generation validation
- Mock-based testing for system command interactions

## External Dependencies

### Python Libraries
- **requests** - HTTP client for downloading version database and documentation scraping
- **trafilatura** - Web content extraction for AWS documentation scraping
- **json** - Native JSON handling for version database management
- **subprocess** - System command execution for package detection
- **pathlib** - Modern path handling for file operations

### System Dependencies
- **Package Managers**: apt-get/apt (Ubuntu/Debian), yum (RHEL/Amazon Linux)
- **Package Query Tools**: dpkg, rpm for installed package detection
- **System Commands**: pip, python3 for Python package management

### External Services
- **GitHub Repository** - Version database hosting and distribution
- **AWS Neuron Documentation** - Source for package version information scraping
- **Neuron Package Repositories** - apt.repos.neuron.amazonaws.com for package installation

### Operating System Support
- **Ubuntu/Debian** - Primary support with apt package manager
- **RHEL/Amazon Linux** - Secondary support with yum package manager
- **Virtual Environment Detection** - `/opt` directory scanning for Neuron virtual environments