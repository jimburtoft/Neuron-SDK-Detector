"""
Package Detection Module

Detects installed AWS Neuron packages from system and Python environments.
"""

import subprocess
import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional


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


# Test the detector if run directly
if __name__ == '__main__':
    detector = PackageDetector()
    
    print("System Packages:")
    system_packages = detector.get_system_packages()
    for name, version in system_packages.items():
        print(f"  {name}: {version}")
    
    print("\nPython Packages (current env):")
    python_packages = detector.get_python_packages()
    for name, version in python_packages.items():
        print(f"  {name}: {version}")
    
    print("\nVirtual Environments in /opt:")
    venv_packages = detector.get_venv_packages('/opt')
    for venv_path, packages in venv_packages.items():
        print(f"  {venv_path}: {len(packages)} packages")
        for name, version in list(packages.items())[:3]:
            print(f"    {name}: {version}")
