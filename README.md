# AWS Neuron SDK Management Suite

A comprehensive Python CLI toolset for detecting, analyzing, and updating AWS Neuron SDK packages across system and virtual environments.

## Overview

The AWS Neuron SDK consists of multiple system packages and Python packages, each with their own versioning scheme. This toolset provides:

1. **Version Detection**: Identifies installed Neuron packages and matches them to SDK releases
2. **Update Script Generation**: Creates intelligent update scripts for specific SDK versions  
3. **Package Analysis**: Compares installed versions against known SDK releases
4. **Mixed Installation Detection**: Identifies when packages from multiple SDK versions are present

## Features

### Detection Tool (`neuron_detector.py`)
- **System Package Detection**: Detects Neuron packages installed via apt/dpkg/rpm
- **Python Package Detection**: Scans pip-installed packages in current and virtual environments  
- **Multi-Environment Support**: Scans virtual environments in `/opt` directory with selective targeting
- **Anchor-Based Detection**: Uses neuronx-cc/neuron-cc versions as authoritative SDK indicators
- **Mixed Installation Detection**: Identifies when packages from multiple SDK versions are present
- **Unknown Version Warning**: Highlights packages with versions not found in any known SDK
- **Multiple Output Modes**: Simple, verbose, script-friendly, and information modes
- **Visual Indicators**: Emphasis characters for out-of-date and unknown packages

### Update Script Generator (`neuron_update.py`) ⭐ **NEW**
- **Intelligent Update Scripts**: Generates bash scripts to update packages to target SDK versions
- **Package Manager Detection**: Auto-detects apt vs yum with proper repository setup
- **Version Wildcards**: Handles repository version suffixes (e.g., `2.27.34.0-ec8cd5e8b`)
- **Upgrade & Downgrade Support**: Supports both upgrading and downgrading SDK versions
- **Held Package Handling**: Automatically handles packages pinned to specific versions
- **Script Mode (Default)**: Outputs analysis as bash comments for direct script execution
- **Virtual Environment Support**: Optional inclusion of virtual environment updates
- **Direct Execution**: `python3 neuron_update.py | bash` for immediate updates

### Database Management
- **Automatic Downloads**: Version database auto-downloads from GitHub when needed
- **Documentation Scraping**: Extracts package versions from AWS Neuron documentation
- **Comprehensive Coverage**: Tracks 37+ SDK versions with release dates
- **Local Caching**: Caches database locally for offline use

## Installation

**🚀 Quick Start Options:**

### Option 1: Detection Only
```bash
# Download just the detector script - completely standalone!
wget https://raw.githubusercontent.com/jimburtoft/Neuron-SDK-Detector/main/neuron_detector.py

# Install only dependency (for downloading database)
pip install requests

# Run immediately - database downloads automatically
python3 neuron_detector.py
```

### Option 2: Full SDK Management (Recommended) ⭐
```bash
# Download both detection and update tools
wget https://raw.githubusercontent.com/jimburtoft/Neuron-SDK-Detector/main/neuron_detector.py
wget https://raw.githubusercontent.com/jimburtoft/Neuron-SDK-Detector/main/neuron_update.py

# Install only dependency (for downloading database)
pip install requests

# Detect current installation
python3 neuron_detector.py

# Generate and run update script to latest SDK
python3 neuron_update.py | bash
```

### Full Repository (For Development)
The complete repository includes:
- `neuron_detector.py` - **Main detection tool**
- `neuron_update.py` - **Update script generator** ⭐ **NEW**
- `neuron_database_updater.py` - Database maintenance utility
- `neuron_versions.json` - Pre-built database (automatically downloaded)
- `README.md` - Documentation
- Test suites with 100% pass rates

```bash
# Clone full repository
git clone https://github.com/jimburtoft/Neuron-SDK-Detector.git
cd Neuron-SDK-Detector

# For database maintenance (optional)
pip install requests trafilatura
```

No complex installation required - both tools are self-contained and auto-download dependencies.

## Usage

### Detection Tool (`neuron_detector.py`)

#### Basic Detection
```bash
# Simple output - just show the detected SDK version
python3 neuron_detector.py
# Output: Neuron SDK version 2.25.0

# Verbose output - show all detected packages
python3 neuron_detector.py --verbose
# Shows detailed breakdown of system and Python packages

# Scan virtual environments in /opt directory
python3 neuron_detector.py --check-venvs

# Target specific virtual environment
python3 neuron_detector.py --check-venvs pytorch_env
```

#### Advanced Detection
```bash
# Script-friendly output (for automation)
python3 neuron_detector.py --version

# Get SDK information and update instructions
python3 neuron_detector.py --info

# Debug package detection issues
python3 neuron_detector.py --debug

# Use custom database file
python3 neuron_detector.py --data-file custom.json
```

### Update Script Generator (`neuron_update.py`) ⭐ **NEW**

#### Quick Updates
```bash
# Update current environment to latest SDK (script mode default)
python3 neuron_update.py

# Direct execution - generate and run update script immediately
python3 neuron_update.py | bash

# Update to specific SDK version
python3 neuron_update.py --version 2.24.0 | bash

# Include virtual environment updates
python3 neuron_update.py --check-venvs | bash
```

#### Script Management
```bash
# Save update script to file
python3 neuron_update.py --output update_to_latest.sh
chmod +x update_to_latest.sh
./update_to_latest.sh

# Show detailed analysis (verbose mode)
python3 neuron_update.py --verbose

# Dry run - analyze without generating script
python3 neuron_update.py --dry-run --check-venvs
```

#### Version Management Examples
```bash
# Upgrade from SDK 2.24.0 to 2.25.0
python3 neuron_update.py --version 2.25.0 | bash

# Downgrade from SDK 2.25.0 to 2.23.0 (automatically handles downgrades)
python3 neuron_update.py --version 2.23.0 | bash

# Update with virtual environments included
python3 neuron_update.py --version 2.25.0 --check-venvs | bash
```
