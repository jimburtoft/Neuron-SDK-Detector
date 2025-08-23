#!/usr/bin/env python3
"""
AWS Neuron SDK Version Detection Tool

Standalone script that detects installed AWS Neuron packages and compares them 
against known SDK releases to determine the installed SDK version.

Downloads the version database from GitHub if not found locally.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import requests
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from urllib.parse import urlparse


class PackageDetector:
    """Detects installed Neuron packages on the system."""
    
    # Known Neuron-related package prefixes
    NEURON_SYSTEM_PREFIXES = [
        'aws-neuron',
        'neuron',
    ]
    
    NEURON_PYTHON_PREFIXES = [
        'aws-neuron',
        'neuron',
        'torch-neuron',
        'tensorflow-neuron',
        'jax-neuron', 
        'jax_neuron',
        'transformers-neuron',
        'mx-neuron',
        'mxnet-neuron',
        'libneuron',
        'tensorboard-plugin-neuron',
    ]
    
    def get_system_packages(self) -> Dict[str, str]:
        """Get installed system packages via dpkg."""
        packages = {}
        
        try:
            # Run dpkg to get installed packages
            result = subprocess.run(
                ['dpkg', '-l'],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.splitlines():
                if self._is_neuron_package_line(line):
                    package_info = self._parse_dpkg_line(line)
                    if package_info:
                        name, version = package_info
                        packages[name] = version
                        
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not query system packages: {e}")
        except FileNotFoundError:
            print("Warning: dpkg not found, skipping system package detection")
        
        return packages
    
    def get_python_packages(self, python_path: Optional[str] = None) -> Dict[str, str]:
        """Get installed Python packages via pip."""
        packages = {}
        
        # Use provided python path or current Python
        pip_cmd = [python_path or sys.executable, '-m', 'pip', 'list', '--format=freeze']
        
        try:
            result = subprocess.run(
                pip_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.splitlines():
                if '==' in line:
                    name, version = line.split('==', 1)
                    if self._is_neuron_python_package(name):
                        packages[name] = version
                        
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not query Python packages: {e}")
        except FileNotFoundError:
            print(f"Warning: Python not found at {python_path or sys.executable}")
        
        return packages
    
    def get_venv_packages(self, base_path: str) -> Dict[str, Dict[str, str]]:
        """Get packages from virtual environments in a directory."""
        venv_packages = {}
        base_path_obj = Path(base_path)
        
        if not base_path_obj.exists():
            print(f"Warning: Directory {base_path} does not exist")
            return venv_packages
        
        # Look for virtual environments
        for item in base_path_obj.iterdir():
            if item.is_dir():
                # Check for common venv structures
                python_paths = [
                    item / 'bin' / 'python',
                    item / 'bin' / 'python3',
                    item / 'Scripts' / 'python.exe',  # Windows
                ]
                
                for python_path in python_paths:
                    if python_path.exists():
                        print(f"Scanning virtual environment: {item.name}")
                        packages = self.get_python_packages(str(python_path))
                        if packages:
                            venv_packages[str(item)] = packages
                        break
        
        return venv_packages
    
    def _is_neuron_package_line(self, line: str) -> bool:
        """Check if a dpkg line contains a Neuron package."""
        # dpkg -l format: status name version architecture description
        parts = line.split()
        if len(parts) >= 2:
            package_name = parts[1]
            return any(package_name.startswith(prefix) for prefix in self.NEURON_SYSTEM_PREFIXES)
        return False
    
    def _parse_dpkg_line(self, line: str) -> Optional[tuple]:
        """Parse a dpkg line to extract package name and version."""
        parts = line.split()
        if len(parts) >= 3:
            status = parts[0]
            name = parts[1]
            version = parts[2]
            
            # Only include installed packages
            if status.startswith('ii'):
                return name, version
        
        return None
    
    def _is_neuron_python_package(self, package_name: str) -> bool:
        """Check if a Python package name is Neuron-related."""
        package_name_lower = package_name.lower()
        return any(package_name_lower.startswith(prefix.lower()) 
                  for prefix in self.NEURON_PYTHON_PREFIXES)


class VersionDatabase:
    """Manages SDK version database and package analysis."""
    
    DEFAULT_DATABASE_URL = "https://raw.githubusercontent.com/jimburtoft/Neuron-What-Am-I/main/neuron_versions.json"
    DEFAULT_LOCAL_PATH = "neuron_versions.json"
    
    def __init__(self, database_path: Optional[str] = None):
        self.database_path = database_path or self.DEFAULT_LOCAL_PATH
        self.sdk_data = {}
        self.package_to_sdk_map = {}
    
    def load_database(self) -> bool:
        """Load version database from file or download if needed."""
        local_path = Path(self.database_path)
        
        # Try to load from local file first
        if local_path.exists():
            try:
                with open(local_path, 'r') as f:
                    self.sdk_data = json.load(f)
                self._build_package_map()
                print(f"Loaded database with {len(self.sdk_data)} SDK versions")
                return True
            except Exception as e:
                print(f"Error loading local database: {e}")
        
        # Try to download from GitHub
        try:
            print("Downloading database from GitHub...")
            response = requests.get(self.DEFAULT_DATABASE_URL, timeout=30)
            response.raise_for_status()
            
            self.sdk_data = response.json()
            self._build_package_map()
            
            # Save locally for future use
            self.save_database(self.sdk_data)
            print(f"Downloaded database with {len(self.sdk_data)} SDK versions")
            return True
            
        except Exception as e:
            print(f"Error downloading database: {e}")
            return False
    
    def save_database(self, data: Dict[str, Any]) -> None:
        """Save database to local file."""
        self.sdk_data = data
        self._build_package_map()
        
        with open(self.database_path, 'w') as f:
            json.dump(data, f, indent=2, sort_keys=True)
        
        print(f"Saved database to {self.database_path}")
    
    def _build_package_map(self) -> None:
        """Build reverse mapping from package name+version to SDK versions."""
        self.package_to_sdk_map = {}
        
        for sdk_version, platforms in self.sdk_data.items():
            for platform, packages in platforms.items():
                for package_name, package_version in packages.items():
                    key = f"{package_name}@{package_version}"
                    if key not in self.package_to_sdk_map:
                        self.package_to_sdk_map[key] = []
                    self.package_to_sdk_map[key].append(sdk_version)
    
    def analyze_installed_packages(self, 
                                 system_packages: Dict[str, str],
                                 python_packages: Dict[str, str],
                                 venv_packages: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """Analyze installed packages against known SDK versions."""
        
        # Collect all packages
        all_packages = {}
        all_packages.update(system_packages)
        all_packages.update(python_packages)
        
        for venv_path, packages in venv_packages.items():
            for name, version in packages.items():
                # Use the package if not already found or if this version is newer
                if name not in all_packages or self._is_newer_version(version, all_packages[name]):
                    all_packages[name] = version
        
        # Find SDK matches
        detected_sdks = {}
        unknown_packages = {}
        
        for package_name, package_version in all_packages.items():
            key = f"{package_name}@{package_version}"
            
            if key in self.package_to_sdk_map:
                # Package version matches known SDK(s)
                for sdk_version in self.package_to_sdk_map[key]:
                    if sdk_version not in detected_sdks:
                        detected_sdks[sdk_version] = {}
                    detected_sdks[sdk_version][package_name] = package_version
            else:
                # Check if package name is known but version doesn't match
                if self._is_known_package_name(package_name):
                    unknown_packages[package_name] = package_version
        
        return {
            'detected_sdks': detected_sdks,
            'unknown_packages': unknown_packages,
            'all_packages': all_packages
        }
    
    def _is_newer_version(self, version1: str, version2: str) -> bool:
        """Compare two version strings."""
        try:
            # Simple numeric comparison - split by dots and compare
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            return v1_parts > v2_parts
        except ValueError:
            # If numeric comparison fails, use string comparison
            return version1 > version2
    
    def _is_known_package_name(self, package_name: str) -> bool:
        """Check if a package name is known in any SDK version."""
        for sdk_version, platforms in self.sdk_data.items():
            for platform, packages in platforms.items():
                if package_name in packages:
                    return True
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Detect AWS Neuron SDK version from installed packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Simple output: Neuron SDK version X.XX.X
  %(prog)s --verbose                 # Show all detected package versions
  %(prog)s --check-venvs             # Also scan virtual environments in /opt
  %(prog)s --data-file custom.json   # Use custom version database file
        """
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed package version information'
    )
    
    parser.add_argument(
        '--check-venvs',
        action='store_true',
        help='Scan virtual environments in /opt directory'
    )
    
    parser.add_argument(
        '--data-file',
        type=str,
        help='Path to version database file (downloads if not found)'
    )

    args = parser.parse_args()

    try:
        # Initialize version database
        db = VersionDatabase(args.data_file)
        
        # Load version database
        if not db.load_database():
            print("Error: Could not load or download version database")
            return 1
        
        # Detect installed packages
        detector = PackageDetector()
        
        # Scan system packages
        system_packages = detector.get_system_packages()
        
        # Scan current Python environment
        current_python_packages = detector.get_python_packages()
        
        # Scan virtual environments if requested
        venv_packages = {}
        if args.check_venvs:
            venv_packages = detector.get_venv_packages('/opt')
        
        # Analyze versions
        analysis = db.analyze_installed_packages(
            system_packages,
            current_python_packages,
            venv_packages
        )
        
        # Output results
        if args.verbose:
            print_verbose_output(analysis, system_packages, current_python_packages, venv_packages)
        else:
            print_simple_output(analysis)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


def print_simple_output(analysis):
    """Print simple SDK version output."""
    if not analysis['detected_sdks']:
        print("No Neuron SDK detected")
        return
    
    if len(analysis['detected_sdks']) == 1:
        sdk_version = list(analysis['detected_sdks'].keys())[0]
        print(f"Neuron SDK version {sdk_version}")
    else:
        # Multiple SDKs detected - show the most recent
        latest_sdk = max(analysis['detected_sdks'].keys(), 
                        key=lambda x: [int(i) for i in x.split('.')])
        print(f"Neuron SDK version {latest_sdk} (mixed installation detected)")


def print_verbose_output(analysis, system_packages, current_python_packages, venv_packages):
    """Print detailed package version information."""
    print("=== AWS Neuron SDK Version Analysis ===\n")
    
    # Show detected SDK versions
    if analysis['detected_sdks']:
        print("Detected SDK Versions:")
        for sdk_version, packages in analysis['detected_sdks'].items():
            print(f"  {sdk_version}: {len(packages)} packages")
        print()
    
    # Show system packages
    if system_packages:
        print("System Packages (dpkg):")
        for package_name, version in system_packages.items():
            status = get_package_status(package_name, version, analysis)
            print(f"  {package_name}: {version} {status}")
        print()
    
    # Show current Python environment packages
    if current_python_packages:
        print("Python Packages (current environment):")
        for package_name, version in current_python_packages.items():
            status = get_package_status(package_name, version, analysis)
            print(f"  {package_name}: {version} {status}")
        print()
    
    # Show virtual environment packages
    for venv_path, packages in venv_packages.items():
        if packages:
            print(f"Python Packages ({venv_path}):")
            for package_name, version in packages.items():
                status = get_package_status(package_name, version, analysis)
                print(f"  {package_name}: {version} {status}")
            print()
    
    # Show unknown packages
    if analysis['unknown_packages']:
        print("⚠️  UNKNOWN VERSIONS (not in any known SDK):")
        for package_name, version in analysis['unknown_packages'].items():
            print(f"  {package_name}: {version}")
        print()
    
    # Summary
    if analysis['detected_sdks']:
        if len(analysis['detected_sdks']) == 1:
            sdk_version = list(analysis['detected_sdks'].keys())[0]
            print(f"Overall Assessment: Neuron SDK {sdk_version}")
        else:
            latest_sdk = max(analysis['detected_sdks'].keys(), 
                           key=lambda x: [int(i) for i in x.split('.')])
            print(f"Overall Assessment: Mixed installation, latest detected SDK {latest_sdk}")
    else:
        print("Overall Assessment: No complete Neuron SDK installation detected")


def get_package_status(package_name, version, analysis):
    """Get status indicator for a package."""
    # Check if package is in unknown list
    if package_name in analysis['unknown_packages']:
        return "❌ UNKNOWN VERSION"
    
    # Find which SDK this package version belongs to
    for sdk_version, packages in analysis['detected_sdks'].items():
        if package_name in packages:
            return f"✓ SDK {sdk_version}"
    
    return ""


if __name__ == '__main__':
    sys.exit(main())