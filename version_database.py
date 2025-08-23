"""
Version Database Module

Manages the database of SDK versions and package mappings.
"""

import json
import os
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Set, List
from urllib.parse import urlparse


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
    
    def get_sdk_versions(self) -> List[str]:
        """Get list of all known SDK versions."""
        return sorted(self.sdk_data.keys(), 
                     key=lambda x: [int(i) for i in x.split('.')],
                     reverse=True)
    
    def get_packages_for_sdk(self, sdk_version: str) -> Dict[str, Dict[str, str]]:
        """Get all packages for a specific SDK version."""
        return self.sdk_data.get(sdk_version, {})


# Test the database if run directly
if __name__ == '__main__':
    db = VersionDatabase()
    
    if db.load_database():
        print(f"Database loaded with {len(db.sdk_data)} SDK versions")
        
        # Show available versions
        print("\nAvailable SDK versions:")
        for version in db.get_sdk_versions():
            print(f"  {version}")
        
        # Test analysis with sample data
        sample_system = {'aws-neuronx-dkms': '2.23.9.0'}
        sample_python = {'torch-neuronx': '2.7.0.2.9.9357'}
        
        analysis = db.analyze_installed_packages(sample_system, sample_python, {})
        print(f"\nSample analysis: {analysis}")
    else:
        print("Failed to load database")
