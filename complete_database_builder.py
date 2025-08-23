#!/usr/bin/env python3
"""
Build complete Neuron SDK database from historical documentation
"""

import json
import re
from typing import Dict, List, Any

def parse_historical_content(content: str) -> Dict[str, Any]:
    """Parse the historical content to extract all SDK versions and packages."""
    
    sdk_data = {}
    
    # Find all SDK version sections
    version_pattern = r'Neuron (\d+\.\d+\.\d+)'
    versions = re.findall(version_pattern, content)
    
    print(f"Found {len(versions)} SDK versions in historical data")
    
    for version in versions:
        print(f"Processing SDK {version}...")
        sdk_data[version] = extract_version_packages(content, version)
    
    return sdk_data

def extract_version_packages(content: str, version: str) -> Dict[str, Dict[str, str]]:
    """Extract package information for a specific SDK version."""
    
    platforms = {
        "Trn1": {},
        "Trn2": {},  
        "Inf2": {},
        "Inf1": {}
    }
    
    # Find the section for this version
    version_start = content.find(f'Neuron {version}')
    if version_start == -1:
        return platforms
        
    # Find the next version to limit scope
    next_version_pattern = r'Neuron \d+\.\d+\.\d+'
    next_match = None
    search_start = version_start + len(f'Neuron {version}')
    
    next_matches = list(re.finditer(next_version_pattern, content[search_start:]))
    if next_matches:
        next_match = next_matches[0]
        version_content = content[version_start:search_start + next_match.start()]
    else:
        version_content = content[version_start:]
    
    # Extract packages for each platform
    for platform in platforms.keys():
        platform_packages = extract_platform_packages(version_content, platform)
        if platform_packages:
            platforms[platform] = platform_packages
    
    return platforms

def extract_platform_packages(content: str, platform: str) -> Dict[str, str]:
    """Extract packages for a specific platform from version content."""
    
    packages = {}
    
    # Look for platform section
    platform_pattern = f'{platform} packages'
    platform_start = content.find(platform_pattern)
    
    if platform_start == -1:
        return packages
    
    # Find the next platform or end of section
    next_platform_patterns = ['Trn1 packages', 'Trn2 packages', 'Inf2 packages', 'Inf1 packages', 'Supported Python Versions']
    next_platform_start = len(content)
    
    for pattern in next_platform_patterns:
        if pattern != f'{platform} packages':
            pos = content.find(pattern, platform_start + len(platform_pattern))
            if pos != -1 and pos < next_platform_start:
                next_platform_start = pos
    
    platform_content = content[platform_start:next_platform_start]
    
    # Extract package lines
    lines = platform_content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or 'Component' in line or 'Package' in line:
            continue
            
        # Skip header-like lines
        if line.startswith('#') or 'List of packages' in line:
            continue
            
        # Parse package lines - handle different formats
        # Format: "Component Package-name-version"
        # Format: "Package-name-version"
        
        # Extract package name and version using regex
        package_match = re.search(r'([a-zA-Z0-9_-]+(?:-neuron[a-z]*)?[a-zA-Z0-9_-]*)-(\d+(?:\.\d+)*(?:\.\d+)*(?:\.\w+)*)', line)
        if package_match:
            package_name = package_match.group(1)
            version = package_match.group(2)
            
            # Clean up package name
            if package_name.startswith('aws-'):
                pass  # Keep as-is
            elif package_name in ['neuron-cc', 'neuronx-cc', 'torch-neuron', 'torch-neuronx', 'tensorflow-neuron', 'tensorflow-neuronx']:
                pass  # Keep as-is
            elif package_name.startswith('neuron') or package_name.endswith('neuron'):
                pass  # Keep as-is
            
            packages[package_name] = version
    
    return packages

def load_current_release_data():
    """Load data from current release (2.25.0) that we already have."""
    current_data = {
        "2.25.0": {
            "Trn1": {
                "aws-neuronx-collectives": "2.27.34.0",
                "aws-neuronx-dkms": "2.23.9.0",
                "aws-neuronx-gpsimd-customop-lib": "0.17.1.0",
                "aws-neuronx-gpsimd-tools": "0.17.0.0",
                "aws-neuronx-k8-plugin": "2.27.7.0",
                "aws-neuronx-k8-scheduler": "2.27.7.0",
                "aws-neuronx-oci-hook": "2.11.42.0",
                "aws-neuronx-runtime-discovery": "2.9",
                "aws-neuronx-runtime-lib": "2.27.23.0",
                "aws-neuronx-tools": "2.25.145.0",
                "jax_neuronx": "0.6.1.1.0.3499",
                "libneuronxla": "2.2.8201.0",
                "neuronx-cc": "2.20.9961.0",
                "neuronx-cc-stubs": "2.20.9961.0",
                "neuronx_distributed": "0.14.18461",
                "neuronx_distributed_training": "1.5.0",
                "neuronx_distributed_inference": "0.5.9230",
                "tensorboard-plugin-neuronx": "2.0.813.0",
                "tensorflow-model-server-neuronx": "2.10.1.2.12.2.0",
                "tensorflow-neuronx": "2.10.1.2.1.0",
                "torch-neuronx": "2.7.0.2.9.9357",
                "transformers-neuronx": "0.13.1216"
            },
            "Trn2": {
                "aws-neuronx-collectives": "2.27.34.0",
                "aws-neuronx-dkms": "2.23.9.0",
                "aws-neuronx-gpsimd-customop-lib": "0.17.1.0",
                "aws-neuronx-gpsimd-tools": "0.17.0.0",
                "aws-neuronx-k8-plugin": "2.27.7.0",
                "aws-neuronx-k8-scheduler": "2.27.7.0",
                "aws-neuronx-oci-hook": "2.11.42.0",
                "aws-neuronx-runtime-discovery": "2.9",
                "aws-neuronx-runtime-lib": "2.27.23.0",
                "aws-neuronx-tools": "2.25.145.0",
                "neuronx-cc": "2.20.9961.0",
                "neuronx-cc-stubs": "2.20.9961.0",
                "neuronx_distributed": "0.14.18461",
                "neuronx_distributed_training": "1.5.0",
                "neuronx_distributed_inference": "0.5.9230",
                "torch-neuronx": "2.7.0.2.9.9357"
            },
            "Inf2": {
                "aws-neuronx-collectives": "2.27.34.0",
                "aws-neuronx-dkms": "2.23.9.0",
                "aws-neuronx-gpsimd-customop-lib": "0.17.1.0",
                "aws-neuronx-gpsimd-tools": "0.17.0.0",
                "aws-neuronx-k8-plugin": "2.27.7.0",
                "aws-neuronx-k8-scheduler": "2.27.7.0",
                "aws-neuronx-oci-hook": "2.11.42.0",
                "aws-neuronx-runtime-discovery": "2.9",
                "aws-neuronx-runtime-lib": "2.27.23.0",
                "aws-neuronx-tools": "2.25.145.0",
                "jax_neuronx": "0.6.1.1.0.3499",
                "libneuronxla": "2.2.8201.0",
                "neuronx-cc": "2.20.9961.0",
                "neuronx-cc-stubs": "2.20.9961.0",
                "neuronx_distributed": "0.14.18461",
                "neuronx_distributed_inference": "0.5.9230",
                "tensorboard-plugin-neuronx": "2.0.813.0",
                "tensorflow-model-server-neuronx": "2.10.1.2.12.2.0",
                "tensorflow-neuronx": "2.10.1.2.1.0",
                "torch-neuronx": "2.7.0.2.9.9357",
                "transformers-neuronx": "0.13.1216"
            },
            "Inf1": {
                "aws-neuronx-collectives": "2.27.34.0",
                "aws-neuronx-dkms": "2.23.9.0",
                "aws-neuronx-k8-plugin": "2.27.7.0",
                "aws-neuronx-k8-scheduler": "2.27.7.0",
                "aws-neuronx-oci-hook": "2.11.42.0",
                "aws-neuronx-tools": "2.25.145.0",
                "mx_neuron": "1.8.0.2.4.147.0",
                "mxnet_neuron": "1.5.1.1.10.0.0",
                "neuron-cc": "1.24.0.0",
                "neuronperf": "1.8.93.0",
                "tensorflow-model-server-neuronx": "2.10.1.2.12.2.0",
                "tensorflow-neuron": "2.10.1.2.12.2.0",
                "torch-neuron": "1.13.1.2.11.13.0"
            }
        }
    }
    return current_data

def main():
    """Build complete database from historical and current data."""
    
    print("Building complete Neuron SDK database...")
    
    # Load current release data
    complete_data = load_current_release_data()
    
    # Load and parse historical data
    try:
        with open('historical_content.md', 'r') as f:
            historical_content = f.read()
        
        historical_data = parse_historical_content(historical_content)
        
        # Merge historical data with current data
        for version, platforms in historical_data.items():
            if version not in complete_data:
                complete_data[version] = platforms
        
    except FileNotFoundError:
        print("Historical content file not found, using only current data")
    
    # Save complete database
    with open('neuron_versions.json', 'w') as f:
        json.dump(complete_data, f, indent=2, sort_keys=True)
    
    print(f"\n✅ Complete database saved!")
    print(f"📊 Total SDK versions: {len(complete_data)}")
    
    # Show summary by version (newest first)
    sorted_versions = sorted(complete_data.keys(), key=lambda x: [int(i) for i in x.split('.')], reverse=True)
    
    for version in sorted_versions[:10]:  # Show top 10
        platforms = complete_data[version]
        total_packages = sum(len(packages) for packages in platforms.values() if packages)
        platform_count = len([p for p in platforms.values() if p])
        print(f"  {version}: {total_packages} packages across {platform_count} platforms")
    
    if len(sorted_versions) > 10:
        print(f"  ... and {len(sorted_versions) - 10} more versions")

if __name__ == '__main__':
    main()