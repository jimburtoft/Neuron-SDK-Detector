#!/usr/bin/env python3
"""
AWS Neuron SDK Update Script Generator

Analyzes current Neuron package installations and generates shell scripts
to update only the currently installed packages to the latest SDK version
or a specified target version.

Supports both apt (Ubuntu/Debian) and yum (RHEL/Amazon Linux) package managers.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

# Import from neuron_detector
sys.path.append('.')
from neuron_detector import VersionDatabase, PackageDetector


class PackageManagerDetector:
    """Detects the package manager and distribution."""
    
    @staticmethod
    def detect_package_manager() -> Tuple[str, str]:
        """
        Detect the package manager and distribution.
        
        Returns:
            Tuple of (package_manager, distribution)
        """
        # Check for apt (Debian/Ubuntu)
        if os.path.exists('/usr/bin/apt-get') or os.path.exists('/usr/bin/apt'):
            try:
                # Check if it's Ubuntu
                with open('/etc/os-release', 'r') as f:
                    content = f.read()
                    if 'Ubuntu' in content:
                        return 'apt', 'ubuntu'
                    elif 'Debian' in content:
                        return 'apt', 'debian'
                    else:
                        return 'apt', 'debian'  # Default to debian for apt systems
            except:
                return 'apt', 'debian'
        
        # Check for yum (RHEL/CentOS/Amazon Linux)
        elif os.path.exists('/usr/bin/yum') or os.path.exists('/usr/bin/dnf'):
            try:
                with open('/etc/os-release', 'r') as f:
                    content = f.read()
                    if 'Amazon Linux' in content:
                        return 'yum', 'amazonlinux'
                    elif 'Red Hat' in content or 'RHEL' in content:
                        return 'yum', 'rhel'
                    elif 'CentOS' in content:
                        return 'yum', 'centos'
                    else:
                        return 'yum', 'rhel'  # Default to rhel for yum systems
            except:
                return 'yum', 'rhel'
        
        else:
            # Default fallback
            return 'apt', 'ubuntu'


class NeuronUpdateScriptGenerator:
    """Generates update scripts for Neuron packages."""
    
    def __init__(self, target_sdk: Optional[str] = None, script_mode: bool = True):
        """Initialize the update script generator."""
        self.db = VersionDatabase()
        self.db.load_database(quiet=True)
        self.detector = PackageDetector()
        self.pkg_mgr_detector = PackageManagerDetector()
        self.script_mode = script_mode
        
        # Determine target SDK version
        if target_sdk:
            if target_sdk not in self.db.sdk_data:
                raise ValueError(f"SDK version {target_sdk} not found in database")
            self.target_sdk = target_sdk
        else:
            # Use latest SDK
            self.target_sdk = max(self.db.sdk_data.keys(), key=lambda x: [int(i) for i in x.split('.')])
        
        self._print_info(f"Target SDK version: {self.target_sdk}")
        
        # Get target SDK data
        target_data = self.db.sdk_data[self.target_sdk]
        if isinstance(target_data, dict) and 'platforms' in target_data:
            self.target_packages = target_data['platforms']
        else:
            self.target_packages = target_data
    
    def _print_info(self, message: str):
        """Print information with appropriate formatting for script mode."""
        if self.script_mode:
            print(f"# {message}")
        else:
            print(message)
    
    def detect_current_packages(self, check_venvs: bool = False) -> Dict[str, Any]:
        """Detect currently installed Neuron packages."""
        self._print_info("Detecting currently installed Neuron packages...")
        
        system_packages = self.detector.get_system_packages()
        python_packages = self.detector.get_python_packages() 
        
        # Only scan virtual environments if requested
        venv_packages = {}
        if check_venvs:
            venv_packages = self.detector.get_venv_packages('/opt')
        
        # Analyze packages
        analysis = self.db.analyze_installed_packages(
            system_packages, python_packages, venv_packages
        )
        
        return {
            'system_packages': system_packages,
            'python_packages': python_packages,
            'venv_packages': venv_packages,
            'analysis': analysis
        }
    
    def generate_system_package_updates(self, current_system_packages: Dict[str, str]) -> List[str]:
        """Generate system package update commands."""
        package_manager, distribution = self.pkg_mgr_detector.detect_package_manager()
        
        commands = []
        packages_to_update = []
        
        self._print_info(f"Detected package manager: {package_manager} on {distribution}")
        
        # Find system packages that need updates
        for current_pkg, current_version in current_system_packages.items():
            # Look for this package in target SDK
            target_version = None
            for platform, packages in self.target_packages.items():
                if current_pkg in packages:
                    target_version = packages[current_pkg]
                    break
            
            if target_version and target_version != current_version:
                # Map package name for system installation
                system_pkg_name = self._map_to_system_package_name(current_pkg, distribution)
                if system_pkg_name:
                    # Use version wildcard to match the base version regardless of suffix
                    # This handles cases where repository has version suffixes like -47cc904ea
                    versioned_pkg = f"{system_pkg_name}={target_version}*"
                    packages_to_update.append(versioned_pkg)
                    self._print_info(f"  System package: {current_pkg} {current_version} -> {target_version}")
        
        if packages_to_update:
            commands.append("echo 'Updating system packages...'")
            
            if package_manager == 'apt':
                # Add Neuron repository if needed
                commands.extend([
                    "# Ensure Neuron repository is configured",
                    "if ! grep -q 'apt.repos.neuron.amazonaws.com' /etc/apt/sources.list.d/neuron.list 2>/dev/null; then",
                    "    echo 'Setting up Neuron repository...'",
                    "    wget -qO - https://apt.repos.neuron.amazonaws.com/GPG-PUB-KEY-AMAZON-NEURON.PUB | sudo apt-key add -",
                    "    echo 'deb https://apt.repos.neuron.amazonaws.com/ $(lsb_release -cs) main' | sudo tee /etc/apt/sources.list.d/neuron.list",
                    "fi",
                    "",
                    "sudo apt-get update",
                    f"sudo apt-get install -y --allow-change-held-packages {' '.join(packages_to_update)}"
                ])
            elif package_manager == 'yum':
                # Add Neuron repository if needed  
                commands.extend([
                    "# Ensure Neuron repository is configured",
                    "if [ ! -f /etc/yum.repos.d/neuron.repo ]; then",
                    "    echo 'Setting up Neuron repository...'",
                    "    sudo tee /etc/yum.repos.d/neuron.repo > /dev/null <<EOF",
                    "[neuron]",
                    "name=Neuron YUM Repository",
                    "baseurl=https://yum.repos.neuron.amazonaws.com",
                    "enabled=1",
                    "metadata_expire=0",
                    "EOF",
                    "fi",
                    "",
                    "sudo yum update -y",
                    f"sudo yum install -y {' '.join(packages_to_update)}"
                ])
        
        return commands
    
    def generate_python_package_updates(self, current_python_packages: Dict[str, str], 
                                      current_venv_packages: Optional[Dict[str, Dict[str, str]]] = None) -> List[str]:
        """Generate Python package update commands."""
        commands = []
        
        # Update current environment packages
        python_updates = []
        for current_pkg, current_version in current_python_packages.items():
            target_version = self._find_target_python_version(current_pkg)
            if target_version and target_version != current_version:
                python_updates.append(f"{current_pkg}=={target_version}")
                self._print_info(f"  Python package: {current_pkg} {current_version} -> {target_version}")
        
        if python_updates:
            commands.extend([
                "",
                "echo 'Updating Python packages in current environment...'",
                f"pip install --upgrade {' '.join(python_updates)}"
            ])
        
        # Update virtual environment packages (only if provided)
        if current_venv_packages:
            for venv_path, venv_pkgs in current_venv_packages.items():
                venv_updates = []
                venv_name = Path(venv_path).name
                
                for current_pkg, current_version in venv_pkgs.items():
                    target_version = self._find_target_python_version(current_pkg)
                    if target_version and target_version != current_version:
                        venv_updates.append(f"{current_pkg}=={target_version}")
                
                if venv_updates:
                    commands.extend([
                        "",
                        f"echo 'Updating virtual environment: {venv_name}...'",
                        f"source {venv_path}/bin/activate",
                        f"pip install --upgrade {' '.join(venv_updates)}",
                        "deactivate"
                    ])
                    self._print_info(f"  Virtual env {venv_name}: {len(venv_updates)} packages to update")
        
        return commands
    
    def _map_to_system_package_name(self, neuron_pkg: str, distribution: str) -> Optional[str]:
        """Map Neuron package name to system package name."""
        # Most Neuron system packages use the same name
        # But some might have different naming conventions
        
        # Common system packages that should be installed via package manager
        system_packages = {
            'aws-neuronx-collectives', 'aws-neuronx-dkms', 'aws-neuronx-oci-hook',
            'aws-neuronx-runtime-lib', 'aws-neuronx-tools', 'aws-neuronx-k8-plugin',
            'aws-neuronx-k8-scheduler', 'aws-neuronx-gpsimd-customop-lib',
            'aws-neuronx-gpsimd-tools', 'aws-neuronx-runtime-discovery'
        }
        
        if neuron_pkg in system_packages:
            return neuron_pkg
        
        return None
    
    def _find_target_python_version(self, package_name: str) -> Optional[str]:
        """Find target version for a Python package."""
        # Try normalized package names
        normalized_names = [
            package_name,
            package_name.replace('-', '_'),
            package_name.replace('_', '-')
        ]
        
        for platform, packages in self.target_packages.items():
            for norm_name in normalized_names:
                if norm_name in packages:
                    return packages[norm_name]
        
        return None
    
    def generate_update_script(self, check_venvs: bool = False) -> str:
        """Generate the complete update script."""
        self._print_info(f"Generating update script for SDK {self.target_sdk}...")
        
        current_packages = self.detect_current_packages(check_venvs=check_venvs)
        
        script_lines = [
            "#!/bin/bash",
            f"# AWS Neuron SDK Update Script",
            f"# Generated to update to SDK version {self.target_sdk}",
            f"# Generated on {os.popen('date').read().strip()}",
            "",
            "set -e  # Exit on any error",
            "",
            "echo 'AWS Neuron SDK Update Script'",
            f"echo 'Target SDK version: {self.target_sdk}'",
            "echo '========================================'"
        ]
        
        # Generate system package updates
        system_updates = self.generate_system_package_updates(current_packages['system_packages'])
        if system_updates:
            script_lines.extend([""] + system_updates)
        else:
            script_lines.extend(["", "echo 'No system packages to update'"])
        
        # Generate Python package updates
        venv_packages = current_packages['venv_packages'] if check_venvs else None
        python_updates = self.generate_python_package_updates(
            current_packages['python_packages'], 
            venv_packages
        )
        if python_updates:
            script_lines.extend(python_updates)
        else:
            script_lines.extend(["", "echo 'No Python packages to update'"])
        
        # Add completion message
        script_lines.extend([
            "",
            "echo '========================================'",
            f"echo 'Update to SDK {self.target_sdk} completed!'",
            "echo 'Please restart your applications to use the new packages'"
        ])
        
        return '\n'.join(script_lines)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Generate AWS Neuron SDK update scripts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 neuron_update.py                        # Update current environment (script mode default)
  python3 neuron_update.py --version 2.24.0       # Update to specific SDK version
  python3 neuron_update.py --check-venvs          # Include virtual environments in update
  python3 neuron_update.py --verbose              # Show detailed analysis information
  python3 neuron_update.py --output update.sh     # Save script to file
        """
    )
    
    parser.add_argument(
        '--version', 
        help='Target SDK version (default: latest)',
        metavar='VERSION'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file for the update script (default: stdout)',
        metavar='FILE'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without generating script'
    )
    
    parser.add_argument(
        '--check-venvs',
        action='store_true',
        help='Include virtual environment packages in update script'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed analysis information (disables default script mode)'
    )
    
    args = parser.parse_args()
    
    try:
        # Create script generator (script_mode is default, disabled by --verbose)
        generator = NeuronUpdateScriptGenerator(target_sdk=args.version, script_mode=not args.verbose)
        
        if args.dry_run:
            print("Dry run mode - analyzing current packages...")
            current_packages = generator.detect_current_packages(check_venvs=args.check_venvs)
            
            print(f"\nSystem packages found: {len(current_packages['system_packages'])}")
            for pkg, ver in current_packages['system_packages'].items():
                print(f"  {pkg}: {ver}")
            
            print(f"\nPython packages found: {len(current_packages['python_packages'])}")
            for pkg, ver in current_packages['python_packages'].items():
                print(f"  {pkg}: {ver}")
            
            print(f"\nVirtual environments found: {len(current_packages['venv_packages'])}")
            for venv_path, packages in current_packages['venv_packages'].items():
                venv_name = Path(venv_path).name
                print(f"  {venv_name}: {len(packages)} packages")
            
            return 0
        
        # Generate update script
        script_content = generator.generate_update_script(check_venvs=args.check_venvs)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(script_content)
            os.chmod(args.output, 0o755)  # Make executable
            print(f"\nUpdate script saved to: {args.output}")
            print("Run the script with: bash {args.output}")
        else:
            if args.verbose:
                print("\n" + "="*50)
                print("GENERATED UPDATE SCRIPT:")
                print("="*50)
            print(script_content)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())