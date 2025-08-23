#!/usr/bin/env python3
"""
AWS Neuron SDK Version Detection Tool

This tool detects installed AWS Neuron packages and compares them against
known SDK releases to determine the installed SDK version.
"""

import argparse
import sys
import json
import os
from pathlib import Path
from package_detector import PackageDetector
from version_database import VersionDatabase
from scraper import NeuronDocumentationScraper


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
  %(prog)s --update-db               # Update version database from AWS docs
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
        '--update-db',
        action='store_true',
        help='Update version database from AWS documentation'
    )

    args = parser.parse_args()

    try:
        # Initialize version database
        db = VersionDatabase(args.data_file)
        
        # Update database if requested
        if args.update_db:
            print("Updating version database from AWS documentation...")
            scraper = NeuronDocumentationScraper()
            sdk_data = scraper.scrape_all_versions()
            db.save_database(sdk_data)
            print("Database updated successfully.")
            return 0
        
        # Load version database
        if not db.load_database():
            print("Downloading version database from AWS documentation...")
            scraper = NeuronDocumentationScraper()
            sdk_data = scraper.scrape_all_versions()
            db.save_database(sdk_data)
            print("Database downloaded successfully.")
        
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
