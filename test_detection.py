#!/usr/bin/env python3
"""
Test the Neuron SDK version detection system with simulated data
"""

from version_database import VersionDatabase
import sys

def test_detection_with_mock_packages():
    """Test the detection system with simulated package installations."""
    
    # Load the database
    db = VersionDatabase()
    if not db.load_database():
        print("Error: Could not load database")
        return
    
    print("=== Testing AWS Neuron SDK Detection System ===\n")
    print(f"Loaded database with {len(db.sdk_data)} SDK versions\n")
    
    # Test case 1: Perfect 2.25.0 installation (Inf2)
    print("Test Case 1: Complete Neuron 2.25.0 installation (Inf2)")
    print("=" * 50)
    
    mock_system_packages = {
        'aws-neuronx-dkms': '2.23.9.0',
        'aws-neuronx-collectives': '2.27.34.0',
        'aws-neuronx-tools': '2.25.145.0'
    }
    
    mock_python_packages = {
        'torch-neuronx': '2.7.0.2.9.9357',
        'neuronx-cc': '2.20.9961.0',
        'transformers-neuronx': '0.13.1216'
    }
    
    analysis = db.analyze_installed_packages(
        mock_system_packages, 
        mock_python_packages, 
        {}
    )
    
    print_analysis_results(analysis, mock_system_packages, mock_python_packages, {})
    
    # Test case 2: Mixed installation (different SDK versions)
    print("\n" + "=" * 60)
    print("Test Case 2: Mixed installation (packages from different SDKs)")
    print("=" * 60)
    
    mixed_system_packages = {
        'aws-neuronx-dkms': '2.23.9.0',  # From 2.25.0
        'aws-neuronx-tools': '2.24.54.0'  # From 2.24.0
    }
    
    mixed_python_packages = {
        'torch-neuronx': '2.7.0.2.9.9357',  # From 2.25.0
        'neuronx-cc': '2.19.8089.0'  # From 2.24.0
    }
    
    mixed_analysis = db.analyze_installed_packages(
        mixed_system_packages,
        mixed_python_packages,
        {}
    )
    
    print_analysis_results(mixed_analysis, mixed_system_packages, mixed_python_packages, {})
    
    # Test case 3: Unknown package versions
    print("\n" + "=" * 60)
    print("Test Case 3: Installation with unknown package versions")
    print("=" * 60)
    
    unknown_packages = {
        'aws-neuronx-dkms': '2.23.9.0',  # Known
        'torch-neuronx': '2.8.0.1.0.0',  # Unknown version
        'neuronx-cc': '2.21.0.0',  # Unknown version
    }
    
    unknown_analysis = db.analyze_installed_packages(
        unknown_packages,
        {},
        {}
    )
    
    print_analysis_results(unknown_analysis, unknown_packages, {}, {})


def print_analysis_results(analysis, system_packages, python_packages, venv_packages):
    """Print formatted analysis results."""
    
    if analysis['detected_sdks']:
        print("Detected SDK Versions:")
        for sdk_version, packages in analysis['detected_sdks'].items():
            print(f"  ✓ {sdk_version}: {len(packages)} matching packages")
        print()
    
    if system_packages:
        print("System Packages (dpkg):")
        for name, version in system_packages.items():
            status = get_package_status(name, version, analysis)
            print(f"  {name}: {version} {status}")
        print()
    
    if python_packages:
        print("Python Packages:")
        for name, version in python_packages.items():
            status = get_package_status(name, version, analysis)
            print(f"  {name}: {version} {status}")
        print()
    
    if analysis['unknown_packages']:
        print("⚠️  UNKNOWN VERSIONS:")
        for name, version in analysis['unknown_packages'].items():
            print(f"  {name}: {version} ❌ UNKNOWN VERSION")
        print()
    
    # Summary
    if analysis['detected_sdks']:
        if len(analysis['detected_sdks']) == 1:
            sdk_version = list(analysis['detected_sdks'].keys())[0]
            print(f"🎯 Result: Neuron SDK {sdk_version}")
        else:
            latest_sdk = max(analysis['detected_sdks'].keys(), 
                           key=lambda x: [int(i) for i in x.split('.')])
            print(f"⚠️  Result: Mixed installation, latest detected SDK {latest_sdk}")
    else:
        print("❌ Result: No complete Neuron SDK installation detected")


def get_package_status(package_name, version, analysis):
    """Get status indicator for a package."""
    if package_name in analysis['unknown_packages']:
        return "❌ UNKNOWN"
    
    for sdk_version, packages in analysis['detected_sdks'].items():
        if package_name in packages:
            return f"✓ SDK {sdk_version}"
    
    return ""


if __name__ == '__main__':
    test_detection_with_mock_packages()