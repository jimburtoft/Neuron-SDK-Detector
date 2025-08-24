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
        'aws-neuronx',
        'aws_neuron',
        'aws_neuronx',
        'neuron',
    ]
    
    NEURON_PYTHON_PREFIXES = [
        'aws-neuron',
        'aws_neuron', 
        'neuron',
        'torch-neuron',
        'torch_neuron',
        'tensorflow-neuron',
        'tensorflow_neuron',
        'jax-neuron', 
        'jax_neuron',
        'transformers-neuron',
        'transformers_neuron',
        'mx-neuron',
        'mx_neuron',
        'mxnet-neuron',
        'mxnet_neuron',
        'libneuron',
        'tensorboard-plugin-neuron',
        'tensorboard_plugin_neuron',
    ]
    
    def get_system_packages(self) -> Dict[str, str]:
        """Get installed system packages via apt/dpkg (Ubuntu/Debian) or rpm (Amazon Linux/RHEL)."""
        packages = {}
        
        # Try apt list first (Ubuntu/Debian) - more reliable than dpkg
        try:
            result = subprocess.run(
                ['apt', 'list', '--installed'],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.splitlines():
                if self._is_neuron_package_line_apt(line):
                    package_info = self._parse_apt_line(line)
                    if package_info:
                        name, version = package_info
                        # Clean system package versions too (remove build suffixes)
                        clean_version = self._clean_version(version)
                        packages[name] = clean_version
                        
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to dpkg if apt is not available
            try:
                result = subprocess.run(
                    ['dpkg', '-l'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                for line in result.stdout.splitlines():
                    if self._is_neuron_package_line_dpkg(line):
                        package_info = self._parse_dpkg_line(line)
                        if package_info:
                            name, version = package_info
                            # Clean system package versions too (remove build suffixes)
                            clean_version = self._clean_version(version)
                            packages[name] = clean_version
                            
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Try rpm if dpkg is not available (Amazon Linux/RHEL)
                try:
                    result = subprocess.run(
                        ['rpm', '-qa', '--queryformat', '%{NAME}\t%{VERSION}-%{RELEASE}\n'],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    for line in result.stdout.splitlines():
                        if self._is_neuron_package_line_rpm(line):
                            package_info = self._parse_rpm_line(line)
                            if package_info:
                                name, version = package_info
                                # Clean system package versions too (remove build suffixes)
                                clean_version = self._clean_version(version)
                                packages[name] = clean_version
                                
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("Warning: No package manager found (apt/dpkg/rpm), skipping system package detection")
        
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
                        # Strip build suffixes (like +f46ac1ef) for database matching
                        clean_version = self._clean_version(version)
                        packages[name] = clean_version
                        
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
    
    def _is_neuron_package_line_apt(self, line: str) -> bool:
        """Check if an apt list line contains a Neuron package."""
        # apt list format: package_name/repo,version architecture [status]
        if '/' in line:
            package_name = line.split('/')[0]
            return any(package_name.startswith(prefix) for prefix in self.NEURON_SYSTEM_PREFIXES)
        return False
    
    def _is_neuron_package_line_dpkg(self, line: str) -> bool:
        """Check if a dpkg line contains a Neuron package."""
        # dpkg -l format: status name version architecture description
        parts = line.split()
        if len(parts) >= 2:
            package_name = parts[1]
            return any(package_name.startswith(prefix) for prefix in self.NEURON_SYSTEM_PREFIXES)
        return False
    
    def _is_neuron_package_line_rpm(self, line: str) -> bool:
        """Check if an rpm line contains a Neuron package."""
        # rpm format: package_name\tversion-release
        if '\t' in line:
            package_name = line.split('\t')[0]
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
    
    def _parse_rpm_line(self, line: str) -> Optional[tuple]:
        """Parse an rpm line to extract package name and version."""
        if '\t' in line:
            parts = line.split('\t')
            if len(parts) >= 2:
                name = parts[0].strip()
                version = parts[1].strip()
                return name, version
        return None
    
    def _parse_apt_line(self, line: str) -> Optional[tuple]:
        """Parse an apt list line to extract package name and version."""
        # apt list format: package_name/repo,status version architecture [status]
        # Example: aws-neuronx-collectives/unknown,now 2.27.34.0-ec8cd5e8b amd64 [installed]
        if '/' in line and ',' in line:
            parts = line.split('/')
            if len(parts) >= 2:
                name = parts[0].strip()
                
                # Extract version from "repo,status version architecture [status]"
                repo_status_version_part = parts[1]
                if ',' in repo_status_version_part:
                    # Split on comma and get everything after it: "status version architecture [status]"
                    status_version_part = repo_status_version_part.split(',', 1)[1].strip()
                    # Split on space and get the part that looks like a version (contains dots or numbers)
                    parts_after_comma = status_version_part.split()
                    
                    # Find the version part (usually the second element, after status like "now")
                    for part in parts_after_comma:
                        # Version typically contains dots and numbers
                        if '.' in part and any(c.isdigit() for c in part):
                            return name, part
        return None
    
    def _is_neuron_python_package(self, package_name: str) -> bool:
        """Check if a Python package name is Neuron-related."""
        package_name_lower = package_name.lower()
        return any(package_name_lower.startswith(prefix.lower()) 
                  for prefix in self.NEURON_PYTHON_PREFIXES)
    
    def _clean_version(self, version: str) -> str:
        """Clean version string by removing build suffixes."""
        # Remove common build suffixes like +abc123, +f46ac1ef, etc.
        if '+' in version:
            version = version.split('+')[0]
        # Remove other possible suffixes
        if '-' in version and not version.count('-') > 2:  # Keep semantic versions like 2.1.0-beta
            # Only strip if it looks like a build suffix (has letters/numbers after -)
            parts = version.split('-')
            if len(parts) > 1 and any(c.isalnum() for c in parts[-1]):
                # Check if last part looks like a commit hash or build ID
                last_part = parts[-1]
                if len(last_part) >= 6 and any(c.isdigit() for c in last_part):
                    version = '-'.join(parts[:-1])
        return version


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
        
        for sdk_version, sdk_data in self.sdk_data.items():
            # Handle both old and new JSON structure
            if isinstance(sdk_data, dict) and 'platforms' in sdk_data:
                # New structure with release dates
                platforms = sdk_data['platforms']
            else:
                # Old structure without release dates
                platforms = sdk_data
                
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
                # Package version matches known SDK(s) - pick the newest one
                matching_sdks = self.package_to_sdk_map[key]
                newest_sdk = max(matching_sdks, key=lambda x: [int(i) for i in x.split('.')])
                
                if newest_sdk not in detected_sdks:
                    detected_sdks[newest_sdk] = {}
                detected_sdks[newest_sdk][package_name] = package_version
            else:
                # Package not found in any SDK - add to unknown
                unknown_packages[package_name] = package_version
        
        return {
            'detected_sdks': detected_sdks,
            'unknown_packages': unknown_packages,
            'all_packages': all_packages
        }
    
    def analyze_venv_individually(self, venv_path: str, packages: Dict[str, str]) -> Dict[str, Any]:
        """Analyze a single virtual environment's packages."""
        detected_sdks = {}
        unknown_packages = {}
        package_to_highest_sdk = {}  # Track which SDK each package maps to
        
        for package_name, package_version in packages.items():
            key = f"{package_name}@{package_version}"
            
            if key in self.package_to_sdk_map:
                # Package version matches known SDK(s) - pick the newest one
                matching_sdks = self.package_to_sdk_map[key]
                newest_sdk = max(matching_sdks, key=lambda x: [int(i) for i in x.split('.')])
                
                if newest_sdk not in detected_sdks:
                    detected_sdks[newest_sdk] = {}
                detected_sdks[newest_sdk][package_name] = package_version
                package_to_highest_sdk[package_name] = newest_sdk
            else:
                # Package not found in any SDK - add to unknown
                unknown_packages[package_name] = package_version
        
        return {
            'venv_path': venv_path,
            'detected_sdks': detected_sdks,
            'unknown_packages': unknown_packages,
            'package_to_highest_sdk': package_to_highest_sdk,
            'total_packages': len(packages)
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


_version_database = None  # Global reference to access release dates


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
  %(prog)s --debug                   # Show debug information during detection
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
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Show debug information during detection'
    )

    args = parser.parse_args()

    try:
        # Initialize version database
        db = VersionDatabase(args.data_file)
        global _version_database
        _version_database = db  # Store global reference for release dates
        
        # Load version database
        if not db.load_database():
            print("Error: Could not load or download version database")
            return 1
        
        # Detect installed packages
        detector = PackageDetector()
        
        # Show debug info if requested
        if args.debug:
            print("=== Debug Mode ===")
            print(f"Python prefixes: {detector.NEURON_PYTHON_PREFIXES}")
            print(f"System prefixes: {detector.NEURON_SYSTEM_PREFIXES}")
            print()
        
        # Scan system packages
        system_packages = detector.get_system_packages()
        if args.debug:
            print(f"System packages found: {len(system_packages)}")
            for name, ver in system_packages.items():
                print(f"  {name}: {ver}")
            print()
        
        # Scan current Python environment
        current_python_packages = detector.get_python_packages()
        if args.debug:
            print(f"Python packages found: {len(current_python_packages)}")
            for name, ver in current_python_packages.items():
                print(f"  {name}: {ver}")
            print()
        
        # Scan virtual environments if requested
        venv_packages = {}
        venv_analyses = []
        if args.check_venvs:
            venv_packages = detector.get_venv_packages('/opt')
            if args.debug:
                print(f"Virtual environment packages: {len(venv_packages)}")
                for venv, pkgs in venv_packages.items():
                    print(f"  {venv}: {len(pkgs)} packages")
                print()
            
            # Analyze each venv individually
            for venv_path, packages in venv_packages.items():
                if packages:  # Only analyze if venv has neuron packages
                    venv_analysis = db.analyze_venv_individually(venv_path, packages)
                    venv_analyses.append(venv_analysis)
        
        # Analyze versions (system + current Python only for overall analysis)
        analysis = db.analyze_installed_packages(
            system_packages,
            current_python_packages,
            {} if args.check_venvs else venv_packages  # Don't double-count if doing individual analysis
        )
        
        # Output results
        if args.verbose:
            print_verbose_output(analysis, system_packages, current_python_packages, venv_packages, venv_analyses)
        elif args.check_venvs:
            print_simple_output(analysis, venv_analyses)
            print_venv_summary(venv_analyses)
        else:
            print_simple_output(analysis, venv_analyses)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


def get_sdk_release_date(sdk_version):
    """Get release date for an SDK version from the database."""
    global _version_database
    if not _version_database:
        return "date unknown"
    
    sdk_data = _version_database.sdk_data.get(sdk_version, {})
    if isinstance(sdk_data, dict) and 'release_date' in sdk_data:
        return sdk_data['release_date']
    return "date unknown"


def print_simple_output(analysis, venv_analyses=None):
    """Print simple SDK version output."""
    # Collect all unknown versions from main analysis and virtual environments
    all_unknown = {}
    
    # Add unknown versions from main analysis
    if 'unknown_packages' in analysis:
        all_unknown.update(analysis['unknown_packages'])
    
    # Add unknown versions from virtual environments
    if venv_analyses:
        for venv_analysis in venv_analyses:
            if 'unknown_packages' in venv_analysis:
                all_unknown.update(venv_analysis['unknown_packages'])
    
    # Determine if we have a clean single SDK installation
    has_unknown_versions = bool(all_unknown)
    has_multiple_sdks = len(analysis['detected_sdks']) > 1
    has_mixed_installation = has_unknown_versions or has_multiple_sdks
    
    if not analysis['detected_sdks']:
        print("No Neuron SDK detected")
        if has_unknown_versions:
            print("\n⚠️  Unknown package versions:")
            for pkg_name, pkg_version in sorted(all_unknown.items()):
                print(f"  {pkg_name}: {pkg_version}")
    elif not has_mixed_installation:
        # Clean single SDK installation - show version with date
        sdk_version = list(analysis['detected_sdks'].keys())[0]
        release_date = get_sdk_release_date(sdk_version)
        print(f"Neuron SDK version {sdk_version} ({release_date})")
    else:
        # Mixed installation or unknown versions - show detailed breakdown
        if analysis['detected_sdks']:
            latest_sdk = max(analysis['detected_sdks'].keys(), 
                            key=lambda x: [int(i) for i in x.split('.')])
            release_date = get_sdk_release_date(latest_sdk)
            print(f"Mixed installation detected (latest: {latest_sdk} {release_date}):")
            
            # Show all known packages by SDK
            for sdk_version in sorted(analysis['detected_sdks'].keys(), 
                                    key=lambda x: [int(i) for i in x.split('.')], reverse=True):
                packages = analysis['detected_sdks'][sdk_version]
                if packages:
                    sdk_date = get_sdk_release_date(sdk_version)
                    print(f"  SDK {sdk_version} ({sdk_date}):")
                    for pkg_name, pkg_version in sorted(packages.items()):
                        print(f"    {pkg_name}: {pkg_version}")
        else:
            print("Mixed installation detected:")
            
        # Show unknown versions
        if all_unknown:
            print("  Unknown versions:")
            for pkg_name, pkg_version in sorted(all_unknown.items()):
                print(f"    {pkg_name}: {pkg_version}")


def print_venv_summary(venv_analyses):
    """Print summary of virtual environment analysis."""
    if not venv_analyses:
        return
        
    print("\n=== Virtual Environment Analysis ===")
    for venv_analysis in venv_analyses:
        venv_name = venv_analysis['venv_path'].split('/')[-1]  # Get just the venv name
        
        if venv_analysis['detected_sdks']:
            if len(venv_analysis['detected_sdks']) == 1:
                sdk_version = list(venv_analysis['detected_sdks'].keys())[0]
                print(f"  {venv_name}: Neuron SDK {sdk_version}")
            else:
                # Multiple SDKs in one venv - show all components with their highest SDK
                print(f"  {venv_name}: Mixed installation:")
                # Get package versions from the detected_sdks
                for pkg_name, highest_sdk in sorted(venv_analysis['package_to_highest_sdk'].items()):
                    # Find the actual package version
                    pkg_version = None
                    for sdk_ver, packages in venv_analysis['detected_sdks'].items():
                        if pkg_name in packages:
                            pkg_version = packages[pkg_name]
                            break
                    print(f"    {pkg_name}: {pkg_version} ({highest_sdk})")
        
        elif venv_analysis['unknown_packages']:
            # Show deviant packages
            unknown_list = [f"{name}:{ver}" for name, ver in venv_analysis['unknown_packages'].items()]
            print(f"  {venv_name}: Unknown versions - {', '.join(unknown_list)}")
        
        else:
            print(f"  {venv_name}: No Neuron packages detected")


def print_verbose_output(analysis, system_packages, current_python_packages, venv_packages, venv_analyses=None):
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
    
    # Show virtual environment analysis
    if venv_analyses:
        print("=== Virtual Environment Analysis ===")
        for venv_analysis in venv_analyses:
            venv_name = venv_analysis['venv_path'].split('/')[-1]
            print(f"\n{venv_name}:")
            
            if venv_analysis['detected_sdks']:
                print(f"  SDK Versions:")
                for sdk_version, packages in venv_analysis['detected_sdks'].items():
                    print(f"    {sdk_version}: {len(packages)} packages")
                    for pkg_name, pkg_version in packages.items():
                        print(f"      {pkg_name}: {pkg_version}")
            
            if venv_analysis['unknown_packages']:
                print(f"  ⚠️ Unknown Versions:")
                for pkg_name, pkg_version in venv_analysis['unknown_packages'].items():
                    print(f"    {pkg_name}: {pkg_version}")
            
            if not venv_analysis['detected_sdks'] and not venv_analysis['unknown_packages']:
                print(f"  No Neuron packages detected")
        print()
    else:
        # Fallback to old format if no individual analyses
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