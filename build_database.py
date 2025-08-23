#!/usr/bin/env python3
"""
Build Neuron SDK version database from provided documentation files.
"""

import json
import re
from typing import Dict, Any

def parse_package_section(content: str, platform: str) -> Dict[str, str]:
    """Parse packages for a specific platform from content."""
    packages = {}
    
    # Find the platform section
    platform_pattern = f'{platform} packages'
    lines = content.split('\n')
    
    in_package_section = False
    in_package_list = False
    
    for line in lines:
        line = line.strip()
        
        # Look for platform section header
        if platform_pattern in line:
            in_package_section = True
            continue
        
        # End of platform section if we hit another platform or major section
        if in_package_section and ('packages' in line or line.startswith('###') or line.startswith('##')):
            if platform_pattern not in line:
                break
        
        # Look for the package list header
        if in_package_section and line.startswith('Component') and 'Package' in line:
            in_package_list = True
            continue
        
        # End of package list
        if in_package_list and (line == '' or line.startswith('Copy to clipboard') or 
                              line.startswith('Supported Python') or line.startswith('###')):
            break
        
        # Parse package lines
        if in_package_list and line and not line.startswith('Component'):
            package_info = extract_package_info(line)
            if package_info:
                name, version = package_info
                packages[name] = version
    
    return packages

def extract_package_info(line: str):
    """Extract package name and version from a documentation line."""
    # Skip lines that don't contain packages
    if not line or 'Component' in line or 'Package' in line:
        return None
    
    # Split by multiple spaces
    parts = re.split(r'\s{2,}', line)
    if len(parts) >= 2:
        package_spec = parts[-1].strip()
        
        # Extract package name and version using the last dash before version
        match = re.search(r'^(.+)-(\d+(?:\.\d+)*(?:\.\w+)*)$', package_spec)
        if match:
            package_name = match.group(1)
            version = match.group(2)
            return package_name, version
    
    return None

def parse_version_content(content: str, version: str) -> Dict[str, Dict[str, str]]:
    """Parse all platform packages for a specific SDK version."""
    platforms = ['Trn1', 'Trn2', 'Inf1', 'Inf2']
    version_data = {}
    
    for platform in platforms:
        packages = parse_package_section(content, platform)
        version_data[platform] = packages
    
    return version_data

def build_database_from_files():
    """Build the database from provided documentation files."""
    database = {}
    
    # Process current release file
    print("Processing current release documentation...")
    try:
        with open('attached_assets/content-1755920196460.md', 'r') as f:
            current_content = f.read()
        
        # Extract version from content
        version_match = re.search(r'Neuron (\d+\.\d+\.\d+)', current_content)
        if version_match:
            version = version_match.group(1)
            print(f"Found current version: {version}")
            database[version] = parse_version_content(current_content, version)
    except Exception as e:
        print(f"Error processing current release: {e}")
    
    # Process previous releases file
    print("Processing previous releases documentation...")
    try:
        with open('attached_assets/content-1755920229867.md', 'r') as f:
            previous_content = f.read()
        
        # Find all SDK versions in previous releases
        version_matches = re.finditer(r'Neuron (\d+\.\d+\.\d+)', previous_content)
        
        for match in version_matches:
            version = match.group(1)
            if version not in database:  # Don't overwrite current release
                print(f"Found previous version: {version}")
                
                # Extract content for this version
                start_pos = match.start()
                remaining_content = previous_content[start_pos:]
                
                # Find next version or end
                next_match = re.search(r'Neuron \d+\.\d+\.\d+', remaining_content[len(match.group(0)):])
                if next_match:
                    end_pos = len(match.group(0)) + next_match.start()
                    version_content = remaining_content[:end_pos]
                else:
                    version_content = remaining_content
                
                database[version] = parse_version_content(version_content, version)
    
    except Exception as e:
        print(f"Error processing previous releases: {e}")
    
    return database

def main():
    """Build and save the database."""
    print("Building AWS Neuron SDK version database...")
    
    database = build_database_from_files()
    
    # Save to JSON file
    with open('neuron_versions.json', 'w') as f:
        json.dump(database, f, indent=2, sort_keys=True)
    
    print(f"\nDatabase built successfully with {len(database)} SDK versions:")
    for version in sorted(database.keys(), key=lambda x: [int(i) for i in x.split('.')], reverse=True):
        total_packages = sum(len(platform_packages) for platform_packages in database[version].values())
        print(f"  {version}: {total_packages} total packages")
        
        # Show sample packages for the first version
        if version == sorted(database.keys(), key=lambda x: [int(i) for i in x.split('.')], reverse=True)[0]:
            for platform, packages in database[version].items():
                if packages:
                    print(f"    {platform}: {len(packages)} packages")
                    for i, (name, ver) in enumerate(list(packages.items())[:3]):
                        print(f"      {name}: {ver}")
                    if len(packages) > 3:
                        print(f"      ... and {len(packages) - 3} more")

if __name__ == '__main__':
    main()