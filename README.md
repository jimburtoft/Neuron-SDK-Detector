# AWS Neuron SDK Version Detection Tool

A Python CLI toolset for detecting and comparing AWS Neuron SDK package versions across system and virtual environments.

## Overview

The AWS Neuron SDK consists of multiple system packages and Python packages, each with their own versioning scheme. This tool helps users identify which version of the Neuron SDK is installed on their system by:

1. Scraping package version information from AWS documentation
2. Detecting installed Neuron packages (both system and Python)
3. Comparing installed versions against known SDK releases
4. Identifying mixed installations and unknown package versions

## Features

- **System Package Detection**: Detects Neuron packages installed via apt/dpkg
- **Python Package Detection**: Scans pip-installed packages in current and virtual environments
- **Multi-Environment Support**: Scans virtual environments in `/opt` directory
- **Version Database**: Maintains database of package versions for each SDK release
- **Mixed Installation Detection**: Identifies when packages from multiple SDK versions are present
- **Unknown Version Warning**: Highlights packages with versions not found in any known SDK
- **Simple and Verbose Modes**: Choose between quick version check or detailed package listing

## Installation

No installation required - the tool is self-contained Python scripts. Dependencies will be installed automatically when needed.

## Usage

### Basic Usage

```bash
# Simple output - just show the detected SDK version
python3 neuron_version_detector.py
# Output: Neuron SDK version 2.25.0

# Verbose output - show all detected packages
python3 neuron_version_detector.py --verbose
# Shows detailed breakdown of system and Python packages

# Scan virtual environments in /opt directory
python3 neuron_version_detector.py --check-venvs

# Use custom database file
python3 neuron_version_detector.py --data-file custom.json

# Update database from AWS documentation (or use local files)
python3 neuron_version_detector.py --update-db
