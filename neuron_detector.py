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
            
            # Only include installed packages (ii = installed, hi = hold+installed)
            if status.startswith('ii') or status.startswith('hi'):
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
        # apt list format can be:
        # 1. package_name/repo,status version architecture [status] 
        # 2. package_name/status version architecture [status]
        # Example 1: aws-neuronx-collectives/unknown,now 2.27.34.0-ec8cd5e8b amd64 [installed]
        # Example 2: aws-neuronx-collectives/now 2.27.34.0-ec8cd5e8b amd64 [installed,local]
        if '/' in line:
            parts = line.split('/', 1)  # Split only on first '/'
            if len(parts) >= 2:
                name = parts[0].strip()
                after_slash = parts[1].strip()
                
                # Check if there's a comma before any bracket (repo,status format)
                bracket_pos = after_slash.find('[')
                if bracket_pos > 0:
                    before_bracket = after_slash[:bracket_pos].strip()
                    # Look for comma in the part before brackets
                    if ',' in before_bracket:
                        # Format 1: "repo,status version architecture"
                        comma_pos = before_bracket.find(',')
                        version_part = before_bracket[comma_pos + 1:].strip()
                    else:
                        # Format 2: "status version architecture"  
                        version_part = before_bracket.strip()
                else:
                    # No brackets, just use everything after slash
                    version_part = after_slash
                
                # Split version part and find the actual version
                parts_after_status = version_part.split()
                
                # Find the version part (contains dots and numbers, skip status words)
                for part in parts_after_status:
                    # Skip status words like 'now', 'stable', etc.
                    if part.lower() in ['now', 'stable', 'testing', 'unstable']:
                        continue
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
    
    def load_database(self, quiet=False) -> bool:
        """Load version database from file or download if needed."""
        local_path = Path(self.database_path)
        
        # Try to load from local file first
        if local_path.exists():
            try:
                with open(local_path, 'r') as f:
                    self.sdk_data = json.load(f)
                self._build_package_map()
                if not quiet:
                    print(f"Loaded database with {len(self.sdk_data)} SDK versions")
                return True
            except Exception as e:
                if not quiet:
                    print(f"Error loading local database: {e}")
        
        # Try to download from GitHub
        try:
            if not quiet:
                print("Downloading database from GitHub...")
            response = requests.get(self.DEFAULT_DATABASE_URL, timeout=30)
            response.raise_for_status()
            
            self.sdk_data = response.json()
            self._build_package_map()
            
            # Save locally for future use
            self.save_database(self.sdk_data, quiet=quiet)
            if not quiet:
                print(f"Downloaded database with {len(self.sdk_data)} SDK versions")
            return True
            
        except Exception as e:
            if not quiet:
                print(f"Error downloading database: {e}")
            return False
    
    def save_database(self, data: Dict[str, Any], quiet=False) -> None:
        """Save database to local file."""
        self.sdk_data = data
        self._build_package_map()
        
        with open(self.database_path, 'w') as f:
            json.dump(data, f, indent=2, sort_keys=True)
        
        if not quiet:
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
        
        return self._analyze_packages_with_anchor(all_packages)
    
    def _find_anchor_sdk(self, packages: Dict[str, str]) -> Optional[str]:
        """Find the anchor SDK version based on neuronx-cc or neuron-cc packages."""
        anchor_packages = ['neuronx-cc', 'neuron-cc', 'neuronx_cc', 'neuron_cc']
        
        for anchor_pkg in anchor_packages:
            if anchor_pkg in packages:
                version = packages[anchor_pkg]
                # Try normalized package names
                normalized_names = [
                    anchor_pkg,
                    anchor_pkg.replace('-', '_'),
                    anchor_pkg.replace('_', '-')
                ]
                
                for norm_name in normalized_names:
                    key = f"{norm_name}@{version}"
                    if key in self.package_to_sdk_map:
                        matching_sdks = self.package_to_sdk_map[key]
                        return max(matching_sdks, key=lambda x: [int(i) for i in x.split('.')])
        
        return None
    
    def _package_exists_in_sdk(self, package_name: str, package_version: str, sdk_version: str) -> bool:
        """Check if a specific package version exists in the given SDK."""
        if sdk_version not in self.sdk_data:
            return False
            
        sdk_data = self.sdk_data[sdk_version]
        platforms = sdk_data.get('platforms', sdk_data) if isinstance(sdk_data, dict) and 'platforms' in sdk_data else sdk_data
        
        # Try normalized package names
        normalized_names = [
            package_name,
            package_name.replace('-', '_'),
            package_name.replace('_', '-')
        ]
        
        for platform, packages in platforms.items():
            for norm_name in normalized_names:
                if norm_name in packages and packages[norm_name] == package_version:
                    return True
        
        return False
    
    def _analyze_packages_with_anchor(self, all_packages: Dict[str, str]) -> Dict[str, Any]:
        """Analyze packages using anchor SDK detection."""
        detected_sdks = {}
        unknown_packages = {}
        
        # Find anchor SDK
        anchor_sdk = self._find_anchor_sdk(all_packages)
        
        for package_name, package_version in all_packages.items():
            # Try normalized package names (both hyphen and underscore versions)
            normalized_names = [
                package_name,
                package_name.replace('-', '_'),
                package_name.replace('_', '-')
            ]
            
            found_match = False
            for norm_name in normalized_names:
                key = f"{norm_name}@{package_version}"
                
                if key in self.package_to_sdk_map:
                    matching_sdks = self.package_to_sdk_map[key]
                    
                    # If we have an anchor SDK and this package exists in the anchor SDK, prefer it
                    if anchor_sdk and anchor_sdk in matching_sdks:
                        target_sdk = anchor_sdk
                    else:
                        # Otherwise use the newest SDK
                        target_sdk = max(matching_sdks, key=lambda x: [int(i) for i in x.split('.')])
                    
                    if target_sdk not in detected_sdks:
                        detected_sdks[target_sdk] = {}
                    detected_sdks[target_sdk][package_name] = package_version
                    found_match = True
                    break
            
            if not found_match:
                # Package not found in any SDK - add to unknown
                unknown_packages[package_name] = package_version
        
        return {
            'detected_sdks': detected_sdks,
            'unknown_packages': unknown_packages,
            'all_packages': all_packages
        }
    
    def analyze_venv_individually(self, venv_path: str, packages: Dict[str, str]) -> Dict[str, Any]:
        """Analyze a single virtual environment's packages."""
        package_to_highest_sdk = {}  # Track which SDK each package maps to
        
        # Use the anchor-based analysis
        analysis = self._analyze_packages_with_anchor(packages)
        
        # Build package to SDK mapping for this venv
        for sdk_version, sdk_packages in analysis['detected_sdks'].items():
            for pkg_name in sdk_packages:
                package_to_highest_sdk[pkg_name] = sdk_version
        
        return {
            'venv_path': venv_path,
            'detected_sdks': analysis['detected_sdks'],
            'unknown_packages': analysis['unknown_packages'],
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
  %(prog)s --check-venvs pytorch     # Scan only pytorch virtual environment
  %(prog)s --version                 # Script-friendly version output (2.25.0)
  %(prog)s --info                    # Show latest SDK info and update instructions
  %(prog)s --info --verbose          # Show all known SDK versions
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
        nargs='?',
        const='all',
        metavar='VENV_NAME',
        help='Scan virtual environments in /opt directory (optionally specify single venv name)'
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
    
    parser.add_argument(
        '--version',
        action='store_true',
        help='Output only the SDK version number for scripting (fails on mixed/no packages)'
    )
    
    parser.add_argument(
        '--info',
        action='store_true',
        help='Display latest SDK info and update instructions'
    )

    args = parser.parse_args()

    try:
        # Initialize version database
        db = VersionDatabase(args.data_file)
        global _version_database
        _version_database = db  # Store global reference for release dates and closest versions
        
        # Load version database (quiet mode for --version flag)
        quiet_mode = args.version
        if not db.load_database(quiet=quiet_mode):
            if not quiet_mode:
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
            
            # Filter to specific venv if specified
            if args.check_venvs != 'all':
                target_venv = args.check_venvs
                # Find matching venv (allow partial matches)
                matching_venvs = {path: packages for path, packages in venv_packages.items() 
                                if target_venv in path.split('/')[-1]}
                if not matching_venvs:
                    print(f"Error: Virtual environment '{target_venv}' not found")
                    return 1
                venv_packages = matching_venvs
            
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
        
        # Handle special flags first
        if args.info:
            print_info_output(args.verbose)
            return 0
        
        if args.version:
            return print_version_output(analysis, venv_analyses)
        
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


def print_info_output(verbose=False):
    """Print SDK info and update instructions."""
    global _version_database
    if not _version_database:
        print("Error: Database not loaded")
        return
    
    # Find latest SDK version
    all_versions = list(_version_database.sdk_data.keys())
    if not all_versions:
        print("Error: No SDK versions found in database")
        return
    
    latest_version = max(all_versions, key=lambda x: [int(i) for i in x.split('.')])
    latest_date = get_sdk_release_date(latest_version)
    
    print(f"AWS Neuron SDK Information")
    print(f"========================")
    print(f"Latest SDK Version: {latest_version} ({latest_date})")
    print(f"Database contains: {len(all_versions)} SDK versions")
    print()
    print("To update the version database:")
    print("  python3 neuron_database_updater.py")
    print()
    print("To update to latest SDK, refer to AWS Neuron documentation:")
    print("  https://awsdocs-neuron.readthedocs-hosted.com/en/latest/")
    
    if verbose:
        print(f"\nAll known SDK versions (newest to oldest):")
        sorted_versions = sorted(all_versions, key=lambda x: [int(i) for i in x.split('.')], reverse=True)
        for version in sorted_versions:
            date = get_sdk_release_date(version)
            print(f"  {version} ({date})")


def print_version_output(analysis, venv_analyses=None):
    """Print only SDK version for scripting (fails on mixed/no packages)."""
    # Collect all unknown versions
    all_unknown = {}
    if 'unknown_packages' in analysis:
        all_unknown.update(analysis['unknown_packages'])
    
    if venv_analyses:
        for venv_analysis in venv_analyses:
            if 'unknown_packages' in venv_analysis:
                all_unknown.update(venv_analysis['unknown_packages'])
    
    # Check for clean single SDK installation
    has_unknown_versions = bool(all_unknown)
    has_multiple_sdks = len(analysis['detected_sdks']) > 1
    
    if not analysis['detected_sdks']:
        print("Error: No Neuron packages detected", file=sys.stderr)
        return 1
    elif has_unknown_versions or has_multiple_sdks:
        print("Error: Mixed installation detected", file=sys.stderr)
        return 1
    else:
        # Clean single SDK installation
        sdk_version = list(analysis['detected_sdks'].keys())[0]
        print(sdk_version)
        return 0


def find_closest_versions(package_name, unknown_version):
    """Find closest known versions above and below an unknown version with SDK info."""
    global _version_database
    if not _version_database:
        return None, None
    
    # Normalize package name (try both hyphen and underscore versions)
    normalized_names = [
        package_name,
        package_name.replace('-', '_'),
        package_name.replace('_', '-')
    ]
    
    # Collect all known versions for this package with their SDK versions
    version_to_sdk = {}
    for sdk_version, sdk_data in _version_database.sdk_data.items():
        if isinstance(sdk_data, dict) and 'platforms' in sdk_data:
            platforms = sdk_data['platforms']
        else:
            platforms = sdk_data
            
        for platform, packages in platforms.items():
            # Check all normalized package name variants
            for norm_name in normalized_names:
                if norm_name in packages:
                    pkg_version = packages[norm_name]
                    if pkg_version not in version_to_sdk:
                        version_to_sdk[pkg_version] = sdk_version
    
    if not version_to_sdk:
        return None, None
    
    # Sort versions using proper version comparison
    unique_versions = list(version_to_sdk.keys())
    try:
        def version_key(v):
            # Split version into numeric components for proper sorting
            parts = []
            for part in v.split('.'):
                if part.isdigit():
                    parts.append(int(part))
                else:
                    parts.append(part)
            return parts
        
        unique_versions.sort(key=version_key)
        
        # Find closest versions
        below_version = None
        below_sdk = None
        above_version = None
        above_sdk = None
        
        # Convert unknown_version for comparison
        unknown_key = version_key(unknown_version)
        
        for version in unique_versions:
            version_key_val = version_key(version)
            if version_key_val < unknown_key:
                below_version = version
                below_sdk = version_to_sdk[version]
            elif version_key_val > unknown_key and above_version is None:
                above_version = version
                above_sdk = version_to_sdk[version]
                break
        
        # Return tuples of (version, sdk) or None
        below_info = (below_version, below_sdk) if below_version else None
        above_info = (above_version, above_sdk) if above_version else None
        
        return below_info, above_info
    except:
        # If version parsing fails, return None
        return None, None


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
                below_info, above_info = find_closest_versions(pkg_name, pkg_version)
                closest_info = ""
                if below_info or above_info:
                    closest_parts = []
                    if below_info:
                        closest_parts.append(f"↓{below_info[0]} (SDK {below_info[1]})")
                    if above_info:
                        closest_parts.append(f"↑{above_info[0]} (SDK {above_info[1]})")
                    closest_info = f" [closest: {', '.join(closest_parts)}]"
                print(f"  ❌ {pkg_name}: {pkg_version}{closest_info}")
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
            latest_sdk = max(analysis['detected_sdks'].keys(), 
                            key=lambda x: [int(i) for i in x.split('.')])
            
            for sdk_version in sorted(analysis['detected_sdks'].keys(), 
                                    key=lambda x: [int(i) for i in x.split('.')], reverse=True):
                packages = analysis['detected_sdks'][sdk_version]
                if packages:
                    sdk_date = get_sdk_release_date(sdk_version)
                    print(f"  SDK {sdk_version} ({sdk_date}):")
                    for pkg_name, pkg_version in sorted(packages.items()):
                        # Add emphasis for out-of-date packages
                        if sdk_version != latest_sdk:
                            print(f"    ⚠️ {pkg_name}: {pkg_version}")
                        else:
                            print(f"    {pkg_name}: {pkg_version}")
        else:
            print("Mixed installation detected:")
            
        # Show unknown versions
        if all_unknown:
            print("  Unknown versions:")
            for pkg_name, pkg_version in sorted(all_unknown.items()):
                below_info, above_info = find_closest_versions(pkg_name, pkg_version)
                closest_info = ""
                if below_info or above_info:
                    closest_parts = []
                    if below_info:
                        closest_parts.append(f"↓{below_info[0]} (SDK {below_info[1]})")
                    if above_info:
                        closest_parts.append(f"↑{above_info[0]} (SDK {above_info[1]})")
                    closest_info = f" [closest: {', '.join(closest_parts)}]"
                print(f"    ❌ {pkg_name}: {pkg_version}{closest_info}")


def print_venv_summary(venv_analyses):
    """Print summary of virtual environment analysis."""
    if not venv_analyses:
        return
        
    print("\n=== Virtual Environment Analysis ===")
    for venv_analysis in venv_analyses:
        venv_name = venv_analysis['venv_path'].split('/')[-1]  # Get just the venv name
        
        # Check if this venv has unknown packages or mixed SDKs
        has_unknown_in_venv = bool(venv_analysis.get('unknown_packages', {}))
        has_multiple_sdks_in_venv = len(venv_analysis['detected_sdks']) > 1
        has_mixed_in_venv = has_unknown_in_venv or has_multiple_sdks_in_venv
        
        if venv_analysis['detected_sdks']:
            if not has_mixed_in_venv:
                # Clean single SDK in this venv
                sdk_version = list(venv_analysis['detected_sdks'].keys())[0]
                release_date = get_sdk_release_date(sdk_version)
                print(f"  {venv_name}: Neuron SDK {sdk_version} ({release_date})")
            else:
                # Mixed installation in this venv - show detailed breakdown
                print(f"  {venv_name}: Mixed installation:")
                
                # Show known packages by SDK
                for sdk_ver in sorted(venv_analysis['detected_sdks'].keys(), 
                                    key=lambda x: [int(i) for i in x.split('.')], reverse=True):
                    packages = venv_analysis['detected_sdks'][sdk_ver]
                    if packages:
                        sdk_date = get_sdk_release_date(sdk_ver)
                        print(f"    SDK {sdk_ver} ({sdk_date}):")
                        for pkg_name, pkg_version in sorted(packages.items()):
                            print(f"      {pkg_name}: {pkg_version}")
                
                # Show unknown packages
                if has_unknown_in_venv:
                    print(f"    Unknown versions:")
                    for pkg_name, pkg_version in sorted(venv_analysis['unknown_packages'].items()):
                        below_info, above_info = find_closest_versions(pkg_name, pkg_version)
                        closest_info = ""
                        if below_info or above_info:
                            closest_parts = []
                            if below_info:
                                closest_parts.append(f"↓{below_info[0]} (SDK {below_info[1]})")
                            if above_info:
                                closest_parts.append(f"↑{above_info[0]} (SDK {above_info[1]})")
                            closest_info = f" [closest: {', '.join(closest_parts)}]"
                        print(f"      ❌ {pkg_name}: {pkg_version}{closest_info}")
        
        elif venv_analysis['unknown_packages']:
            # Show deviant packages with closest versions
            print(f"  {venv_name}: Unknown versions:")
            for pkg_name, pkg_version in sorted(venv_analysis['unknown_packages'].items()):
                below_info, above_info = find_closest_versions(pkg_name, pkg_version)
                closest_info = ""
                if below_info or above_info:
                    closest_parts = []
                    if below_info:
                        closest_parts.append(f"↓{below_info[0]} (SDK {below_info[1]})")
                    if above_info:
                        closest_parts.append(f"↑{above_info[0]} (SDK {above_info[1]})")
                    closest_info = f" [closest: {', '.join(closest_parts)}]"
                print(f"    ❌ {pkg_name}: {pkg_version}{closest_info}")
        
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
                    below_info, above_info = find_closest_versions(pkg_name, pkg_version)
                    closest_info = ""
                    if below_info or above_info:
                        closest_parts = []
                        if below_info:
                            closest_parts.append(f"↓{below_info[0]} (SDK {below_info[1]})")
                        if above_info:
                            closest_parts.append(f"↑{above_info[0]} (SDK {above_info[1]})")
                        closest_info = f" [closest: {', '.join(closest_parts)}]"
                    print(f"    ❌ {pkg_name}: {pkg_version}{closest_info}")
            
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
