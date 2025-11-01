# AWS Neuron SDK Management Suite

A comprehensive toolkit for detecting and updating AWS Neuron SDK packages across system and virtual environments.

## Overview

The AWS Neuron SDK consists of multiple system packages and Python packages, each with their own versioning scheme. This toolset provides:

1. **Version Detection**: Identifies installed Neuron packages and matches them to SDK releases
2. **Ready-to-Use Update Scripts**: Pre-built shell scripts for upgrading to specific SDK versions
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
- **Multiple Output Modes**: Simple, verbose, script-friendly, information, and support modes
- **Support Ticket Output**: Copy-paste friendly format with system info and package lists
- **Visual Indicators**: Emphasis characters for out-of-date and unknown packages

### Update Shell Scripts
- **Ready-to-Use**: Pre-built scripts for common SDK versions (2.23.0 through 2.26.1)
- **Upgrade Only Installed Packages**: Only updates packages that are already installed
- **Safe Updates**: Uses `apt --only-upgrade` and pip existence checks to prevent unwanted installs
- **Version Wildcards**: Handles repository version suffixes (e.g., `2.27.34.0-ec8cd5e8b`)
- **Upgrade & Downgrade Support**: Supports both upgrading and downgrading SDK versions
- **Held Package Handling**: Automatically handles packages pinned to specific versions
- **Fresh Install Mode**: Optional commented sections for full SDK installation

### Database Management
- **Automatic Downloads**: Version database auto-downloads from GitHub when needed
- **Documentation Scraping**: Extracts package versions from AWS Neuron documentation
- **Comprehensive Coverage**: Tracks 39 SDK versions with release dates
- **Local Caching**: Caches database locally for offline use

## Installation

**🚀 Quick Start:**

### Detection Only
```bash
# Download just the detector script - completely standalone!
wget https://raw.githubusercontent.com/jimburtoft/Neuron-SDK-Detector/main/neuron_detector.py

# Install only dependency (for downloading database)
pip install requests

# Run immediately - database downloads automatically
python3 neuron_detector.py
```

### Detection + Updates (Recommended)
```bash
# Download detector and update scripts
wget https://raw.githubusercontent.com/jimburtoft/Neuron-SDK-Detector/main/neuron_detector.py
wget https://raw.githubusercontent.com/jimburtoft/Neuron-SDK-Detector/main/update_to_sdk_2_26_1.sh

# Install only dependency (for downloading database)
pip install requests

# Detect current installation
python3 neuron_detector.py

# Run update script (only updates already-installed packages)
chmod +x update_to_sdk_2_26_1.sh
./update_to_sdk_2_26_1.sh
```

### Full Repository (For Development)
The complete repository includes:
- `neuron_detector.py` - **Main detection tool**
- `update_to_sdk_*.sh` - **Pre-built update scripts** for SDK versions 2.23.0 through 2.26.1
- `neuron_database_updater.py` - Database maintenance utility
- `neuron_versions.json` - Version database (automatically downloaded)
- `README.md` - Documentation
- Test suites with 100% pass rates

```bash
# Clone full repository
git clone https://github.com/jimburtoft/Neuron-SDK-Detector.git
cd Neuron-SDK-Detector

# For database maintenance (optional)
pip install requests trafilatura
```

No complex installation required - the detector is self-contained and auto-downloads dependencies.

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

# Support ticket information (copy-paste friendly)
python3 neuron_detector.py --support

# Debug package detection issues
python3 neuron_detector.py --debug

# Use custom database file
python3 neuron_detector.py --data-file custom.json
```

### Update Scripts

#### Available Update Scripts
- `update_to_sdk_2_23_0.sh` - AWS Neuron SDK 2.23.0 (05/29/2025)
- `update_to_sdk_2_24_0.sh` - AWS Neuron SDK 2.24.0 (07/03/2025)
- `update_to_sdk_2_25_0.sh` - AWS Neuron SDK 2.25.0 (08/07/2025)
- `update_to_sdk_2_26_0.sh` - AWS Neuron SDK 2.26.0 (09/18/2025)
- `update_to_sdk_2_26_1.sh` - AWS Neuron SDK 2.26.1 (10/29/2025)

#### Running Update Scripts
```bash
# Upgrade to SDK 2.26.1 (latest)
chmod +x update_to_sdk_2_26_1.sh
./update_to_sdk_2_26_1.sh

# Upgrade to specific version
chmod +x update_to_sdk_2_25_0.sh
./update_to_sdk_2_25_0.sh

# Downgrade to earlier version (also supported)
chmod +x update_to_sdk_2_23_0.sh
./update_to_sdk_2_23_0.sh
```

#### How Update Scripts Work
The update scripts use **intelligent upgrade logic** that only updates packages you already have installed:

1. **System Packages**: Uses `apt install --only-upgrade` to upgrade only installed packages
2. **Python Packages**: Checks if each package exists with `pip show` before upgrading
3. **Version Wildcards**: Handles repository version suffixes automatically
4. **Held Packages**: Uses `--allow-change-held-packages` to handle pinned versions

**Example: If you only have 3 packages installed, the script will only upgrade those 3 packages - not install all 20+ packages.**

#### Fresh Installation Mode
Each update script includes commented sections at the bottom for **fresh installations**:

```bash
# Uncomment the sections at the end of the script for FRESH INSTALLATION
# This will install ALL packages for that SDK version, not just upgrade existing ones
```

## How It Works

### Anchor-Based Detection
The detector uses "anchor packages" (neuronx-cc for Inf2/Trn1/Trn2, neuron-cc for Inf1) to determine the authoritative SDK version. When a package version appears in multiple SDK releases, it's matched to the SDK indicated by the anchor package, preventing false "mixed installation" warnings.

### Mixed Installation Detection
When packages from different SDK versions are detected (excluding shared components), the tool warns about potential incompatibilities and suggests using an update script to ensure consistency.

### Virtual Environment Scanning
The detector can scan Python virtual environments in `/opt` or target specific environments. This helps identify Neuron packages across multiple isolated Python environments.

## Database Management

### Updating the Version Database
```bash
# Scrape AWS documentation to update version database
python3 neuron_database_updater.py
```

The database updater:
1. Downloads AWS Neuron documentation pages
2. Extracts package version tables using trafilatura
3. Updates `neuron_versions.json` with new SDK versions
4. Validates the extracted data

## Example Output

### Detection Output (Simple)
```
Neuron SDK version 2.25.0
```

### Detection Output (Verbose)
```
AWS Neuron SDK Detection Results
================================
Detected SDK Version: 2.25.0

System Packages (apt):
  ✓ aws-neuronx-dkms = 2.23.0.0
  ✓ aws-neuronx-tools = 2.25.7.0
  ✓ aws-neuronx-runtime-lib = 2.27.30.0

Python Packages (pip):
  ✓ neuronx-cc = 2.20.15193.0
  ✓ torch-neuronx = 2.7.0.2.9.11854
  ✓ transformers-neuronx = 0.12.1248
```

### Support Ticket Output
```
================================================================================
AWS NEURON SUPPORT INFORMATION
================================================================================

## Product Name
$ cat /sys/devices/virtual/dmi/id/product_name
inf2.xlarge

## System Packages
$ apt list | grep neuron | grep installed
aws-neuronx-collectives/unknown,now 2.28.27.0 amd64 [installed]
aws-neuronx-dkms/unknown,now 2.24.7.0 amd64 [installed]
aws-neuronx-tools/unknown,now 2.26.14.0 amd64 [installed]

## Python Packages
$ pip3 list | grep neuron
neuronx-cc                     2.21.33363.0
torch-neuronx                  2.8.0.2.10.16998
transformers-neuronx           0.13.1315

================================================================================
END OF SUPPORT INFORMATION
================================================================================
```

### Update Script Output
```
Updating to AWS Neuron SDK 2.26.1 (10/29/2025)
This script only updates packages that are already installed.

Updating package lists...
Updating system packages (if installed)...
Updating Python packages (if installed)...
Upgrading neuronx-cc...
Upgrading torch-neuronx...

AWS Neuron SDK 2.26.1 update complete!

Bug fixes in SDK 2.26.1:
• Fixed out-of-memory errors in torch-neuronx
• Enabled direct memory allocation via Neuron Runtime API

To verify your installation:
  python3 neuron_detector.py --verbose
```

## Testing

The repository includes comprehensive test suites:

```bash
# Run detector tests
python3 test_neuron_detector.py

# Run package detection tests
python3 test_package_detection.py
```

Tests validate:
- Package detection across different SDK versions
- Anchor-based version matching
- Mixed installation detection logic
- Virtual environment scanning

## Contributing

Contributions are welcome! Please ensure:
1. All tests pass before submitting
2. New features include test coverage
3. Documentation is updated accordingly

## License

This project is provided as-is for use with AWS Neuron SDK management.

## Support

For issues or questions:
1. Check existing GitHub issues
2. Review AWS Neuron SDK documentation
3. Open a new issue with detailed information about your environment

## Version History

- **2.26.1** (November 2025) - Added SDK 2.26.1 support, fixed pip upgrade logic
- **2.26.0** (September 2025) - Added SDK 2.26.0 support
- **2.25.0** (August 2025) - Added SDK 2.25.0 support
- **2.24.0** (July 2025) - Added SDK 2.24.0 support
- **2.23.0** (May 2025) - Initial release with update scripts
