#!/usr/bin/env python3
"""
Build complete Neuron SDK database with proper parsing
"""

import json
import re
from typing import Dict, List, Any

def extract_packages_from_section(content: str, start_marker: str, end_markers: List[str]) -> Dict[str, str]:
    """Extract packages from a specific section of content."""
    
    packages = {}
    start_pos = content.find(start_marker)
    
    if start_pos == -1:
        return packages
    
    # Find end of section
    end_pos = len(content)
    for end_marker in end_markers:
        pos = content.find(end_marker, start_pos + len(start_marker))
        if pos != -1 and pos < end_pos:
            end_pos = pos
    
    section = content[start_pos:end_pos]
    lines = section.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Skip header lines
        if any(header in line for header in ['Component Package', 'List of packages', 'Supported Python']):
            continue
        
        # Extract package using regex - look for package-version pattern at end of line
        package_match = re.search(r'([a-zA-Z0-9_-]+(?:-neuronx?)?[a-zA-Z0-9_-]*)-(\d+(?:\.\d+)*(?:\.\w+)*)\s*$', line)
        if package_match:
            package_name = package_match.group(1)
            version = package_match.group(2)
            packages[package_name] = version
    
    return packages

def extract_version_data(content: str, version: str) -> Dict[str, Dict[str, str]]:
    """Extract all platform data for a specific version."""
    
    platforms = {"Trn1": {}, "Trn2": {}, "Inf2": {}, "Inf1": {}}
    
    # Find version section
    version_header = f'Neuron {version} ('
    version_start = content.find(version_header)
    if version_start == -1:
        return platforms
    
    # Find next version to limit scope
    next_version_pos = len(content)
    for other_line in content[version_start + 100:].split('\n'):
        if re.match(r'Neuron \d+\.\d+\.\d+ \(', other_line):
            next_version_pos = content.find(other_line, version_start + 100)
            break
    
    version_content = content[version_start:next_version_pos]
    
    # Extract packages for each platform
    platform_end_markers = ['Trn1 packages#', 'Trn2 packages#', 'Inf2 packages#', 'Inf1 packages#', 'Supported Python', 'Neuron ']
    
    for platform in platforms.keys():
        platform_marker = f'{platform} packages#'
        packages = extract_packages_from_section(version_content, platform_marker, platform_end_markers)
        if packages:
            platforms[platform] = packages
    
    return platforms

def get_unique_versions(content: str) -> List[str]:
    """Get unique version numbers from content."""
    
    version_matches = re.findall(r'Neuron (\d+\.\d+\.\d+) \(', content)
    return sorted(list(set(version_matches)), key=lambda x: [int(i) for i in x.split('.')], reverse=True)

def main():
    """Build complete database from historical content."""
    
    print("Building complete Neuron SDK database...")
    
    # Start with current 2.25.0 data
    complete_data = {
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
    
    # Parse historical data
    try:
        with open('historical_content.md', 'r') as f:
            historical_content = f.read()
        
        versions = get_unique_versions(historical_content)
        print(f"Found {len(versions)} unique historical versions")
        
        for version in versions:
            if version not in complete_data:
                print(f"Processing SDK {version}...")
                version_data = extract_version_data(historical_content, version)
                
                # Only add if we found some packages
                if any(platform for platform in version_data.values()):
                    complete_data[version] = version_data
        
    except FileNotFoundError:
        print("Historical content not found, using only current data")
    
    # Save complete database
    with open('neuron_versions.json', 'w') as f:
        json.dump(complete_data, f, indent=2, sort_keys=True)
    
    print(f"\n✅ Complete database saved!")
    print(f"📊 Total SDK versions: {len(complete_data)}")
    
    # Show summary
    sorted_versions = sorted(complete_data.keys(), key=lambda x: [int(i) for i in x.split('.')], reverse=True)
    
    for version in sorted_versions:
        platforms = complete_data[version]
        total_packages = sum(len(packages) for packages in platforms.values() if packages)
        active_platforms = [name for name, packages in platforms.items() if packages]
        
        if total_packages > 0:
            print(f"  {version}: {total_packages} packages ({', '.join(active_platforms)})")

if __name__ == '__main__':
    main()