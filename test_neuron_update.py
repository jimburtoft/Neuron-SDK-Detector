#!/usr/bin/env python3
"""
Functional Tests for AWS Neuron SDK Update Script Generator

Tests the neuron_update.py script generation functionality with various
real-world scenarios and package configurations.
"""

import json
import sys
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import patch, MagicMock

# Import the neuron update script
sys.path.append('.')
from neuron_update import NeuronUpdateScriptGenerator, PackageManagerDetector


class TestNeuronUpdate:
    """Test class for Neuron update script generation."""
    
    def __init__(self):
        """Initialize test environment."""
        self.test_results = []
        
    def run_all_tests(self):
        """Run all test scenarios."""
        print("🧪 Running AWS Neuron Update Script Tests")
        print("=" * 60)
        
        # Test scenarios
        test_methods = [
            self.test_package_manager_detection,
            self.test_system_package_updates,
            self.test_python_package_updates,
            self.test_target_sdk_version,
            self.test_mixed_package_scenario,
            self.test_no_packages_scenario,
            self.test_script_generation,
            self.test_venv_package_updates,
            self.test_apt_vs_yum_commands,
            self.test_edge_cases,
            self.test_real_system_scenario
        ]
        
        for test_method in test_methods:
            try:
                test_method()
                self.test_results.append((test_method.__name__, True, None))
            except Exception as e:
                self.test_results.append((test_method.__name__, False, str(e)))
                print(f"❌ {test_method.__name__}: {e}")
        
        self._print_summary()
    
    def test_package_manager_detection(self):
        """Test package manager and distribution detection."""
        print("\n1. Testing Package Manager Detection")
        
        detector = PackageManagerDetector()
        
        # Test with mocked OS detection
        with patch('os.path.exists') as mock_exists, \
             patch('builtins.open', create=True) as mock_open:
            
            # Test Ubuntu/apt detection
            mock_exists.side_effect = lambda path: path == '/usr/bin/apt-get'
            mock_open.return_value.__enter__.return_value.read.return_value = 'Ubuntu 22.04'
            
            pkg_mgr, distro = detector.detect_package_manager()
            assert pkg_mgr == 'apt', f"Expected apt, got {pkg_mgr}"
            assert distro == 'ubuntu', f"Expected ubuntu, got {distro}"
            
            # Test Amazon Linux/yum detection  
            mock_exists.side_effect = lambda path: path == '/usr/bin/yum'
            mock_open.return_value.__enter__.return_value.read.return_value = 'Amazon Linux 2'
            
            pkg_mgr, distro = detector.detect_package_manager()
            assert pkg_mgr == 'yum', f"Expected yum, got {pkg_mgr}"
            assert distro == 'amazonlinux', f"Expected amazonlinux, got {distro}"
        
        print("✅ Package manager detection working correctly")
    
    def test_system_package_updates(self):
        """Test system package update command generation."""
        print("\n2. Testing System Package Updates")
        
        # Mock current system packages
        current_packages = {
            'aws-neuronx-dkms': '2.22.9.0',           # Older version
            'aws-neuronx-tools': '2.24.145.0',        # Older version
            'aws-neuronx-collectives': '2.27.34.0'    # Already latest
        }
        
        generator = NeuronUpdateScriptGenerator(target_sdk='2.25.0')
        
        # Mock package manager detection to return apt/ubuntu
        with patch.object(generator.pkg_mgr_detector, 'detect_package_manager', 
                         return_value=('apt', 'ubuntu')):
            
            commands = generator.generate_system_package_updates(current_packages)
            
            # Should contain apt commands
            command_str = ' '.join(commands)
            assert 'apt-get update' in command_str, "Expected apt-get update command"
            assert 'apt-get install' in command_str, "Expected apt-get install command"
            assert 'aws-neuronx-dkms' in command_str, "Expected outdated package in commands"
            assert 'aws-neuronx-tools' in command_str, "Expected outdated package in commands"
        
        print("✅ System package updates generated correctly")
    
    def test_python_package_updates(self):
        """Test Python package update command generation."""
        print("\n3. Testing Python Package Updates")
        
        current_python_packages = {
            'torch-neuronx': '2.6.0.2.9.9357',        # Older version
            'neuronx-cc': '2.19.8089.0'               # Older version
        }
        
        current_venv_packages = {
            '/opt/aws_neuronx_venv_pytorch': {
                'torch-neuronx': '2.6.0.2.9.9357',
                'libneuronxla': '2.1.8201.0'
            }
        }
        
        generator = NeuronUpdateScriptGenerator(target_sdk='2.25.0')
        commands = generator.generate_python_package_updates(
            current_python_packages, current_venv_packages
        )
        
        command_str = ' '.join(commands)
        assert 'pip install --upgrade' in command_str, "Expected pip upgrade commands"
        assert 'torch-neuronx==' in command_str, "Expected torch-neuronx version pin"
        assert 'source /opt/aws_neuronx_venv_pytorch/bin/activate' in command_str, "Expected venv activation"
        
        print("✅ Python package updates generated correctly")
    
    def test_target_sdk_version(self):
        """Test targeting specific SDK versions."""
        print("\n4. Testing Target SDK Version Selection")
        
        # Test with specific version
        generator_224 = NeuronUpdateScriptGenerator(target_sdk='2.24.0')
        assert generator_224.target_sdk == '2.24.0', "Expected target SDK 2.24.0"
        
        # Test with latest (default)
        generator_latest = NeuronUpdateScriptGenerator()
        assert generator_latest.target_sdk == '2.25.0', "Expected latest SDK 2.25.0"
        
        # Test with invalid version
        try:
            NeuronUpdateScriptGenerator(target_sdk='99.99.99')
            assert False, "Should have raised error for invalid SDK version"
        except ValueError as e:
            assert 'not found in database' in str(e)
        
        print("✅ Target SDK version selection working correctly")
    
    def test_mixed_package_scenario(self):
        """Test mixed package scenario (system + Python + venv)."""
        print("\n5. Testing Mixed Package Scenario")
        
        # Mock detection of mixed packages
        generator = NeuronUpdateScriptGenerator(target_sdk='2.25.0')
        
        with patch.object(generator, 'detect_current_packages') as mock_detect:
            mock_detect.return_value = {
                'system_packages': {'aws-neuronx-dkms': '2.22.9.0'},
                'python_packages': {'neuronx-cc': '2.19.8089.0'},
                'venv_packages': {'/opt/test_venv': {'torch-neuronx': '2.6.0.2.9.9357'}},
                'analysis': {}
            }
            
            with patch.object(generator.pkg_mgr_detector, 'detect_package_manager',
                             return_value=('apt', 'ubuntu')):
                
                script = generator.generate_update_script()
                
                # Should contain all types of updates
                assert 'apt-get' in script, "Expected system package commands"
                assert 'pip install --upgrade' in script, "Expected Python package commands"
                assert 'source /opt/test_venv' in script, "Expected venv commands"
        
        print("✅ Mixed package scenario handled correctly")
    
    def test_no_packages_scenario(self):
        """Test scenario with no packages to update."""
        print("\n6. Testing No Packages Scenario")
        
        generator = NeuronUpdateScriptGenerator(target_sdk='2.25.0')
        
        with patch.object(generator, 'detect_current_packages') as mock_detect:
            mock_detect.return_value = {
                'system_packages': {},
                'python_packages': {},
                'venv_packages': {},
                'analysis': {}
            }
            
            script = generator.generate_update_script()
            
            assert 'No system packages to update' in script, "Expected no system packages message"
            assert 'No Python packages to update' in script, "Expected no Python packages message"
        
        print("✅ No packages scenario handled correctly")
    
    def test_script_generation(self):
        """Test complete script generation structure.""" 
        print("\n7. Testing Script Generation Structure")
        
        generator = NeuronUpdateScriptGenerator(target_sdk='2.24.0')
        
        with patch.object(generator, 'detect_current_packages') as mock_detect:
            mock_detect.return_value = {
                'system_packages': {'aws-neuronx-dkms': '2.22.9.0'},
                'python_packages': {},
                'venv_packages': {},
                'analysis': {}
            }
            
            with patch.object(generator.pkg_mgr_detector, 'detect_package_manager',
                             return_value=('apt', 'ubuntu')):
                
                script = generator.generate_update_script()
                
                # Check script structure
                assert script.startswith('#!/bin/bash'), "Expected bash shebang"
                assert 'SDK version 2.24.0' in script, "Expected target SDK version"
                assert 'set -e' in script, "Expected error handling"
                assert 'completed!' in script, "Expected completion message"
        
        print("✅ Script generation structure correct")
    
    def test_venv_package_updates(self):
        """Test virtual environment package updates."""
        print("\n8. Testing Virtual Environment Package Updates")
        
        generator = NeuronUpdateScriptGenerator(target_sdk='2.25.0')
        
        venv_packages = {
            '/opt/aws_neuronx_venv_pytorch': {
                'torch-neuronx': '2.6.0.2.9.9357',    # Needs update
                'neuronx-cc': '2.20.9961.0'           # Already latest
            },
            '/opt/aws_neuronx_venv_jax': {
                'jax-neuronx': '0.6.0.1.0.1296'       # Needs update
            }
        }
        
        commands = generator.generate_python_package_updates({}, venv_packages)
        command_str = ' '.join(commands)
        
        # Should update both venvs but only outdated packages
        assert 'aws_neuronx_venv_pytorch' in command_str, "Expected pytorch venv update"
        assert 'aws_neuronx_venv_jax' in command_str, "Expected jax venv update"
        assert 'torch-neuronx==' in command_str, "Expected torch update"
        assert 'jax-neuronx==' in command_str, "Expected jax update"
        
        print("✅ Virtual environment updates working correctly")
    
    def test_apt_vs_yum_commands(self):
        """Test different package manager command generation."""
        print("\n9. Testing APT vs YUM Command Generation")
        
        generator = NeuronUpdateScriptGenerator(target_sdk='2.25.0')
        current_packages = {'aws-neuronx-dkms': '2.22.9.0'}
        
        # Test APT commands
        with patch.object(generator.pkg_mgr_detector, 'detect_package_manager',
                         return_value=('apt', 'ubuntu')):
            apt_commands = generator.generate_system_package_updates(current_packages)
            apt_str = ' '.join(apt_commands)
            assert 'apt-get update' in apt_str, "Expected apt-get update"
            assert 'apt-get install' in apt_str, "Expected apt-get install"
        
        # Test YUM commands
        with patch.object(generator.pkg_mgr_detector, 'detect_package_manager',
                         return_value=('yum', 'amazonlinux')):
            yum_commands = generator.generate_system_package_updates(current_packages)
            yum_str = ' '.join(yum_commands)
            assert 'yum update' in yum_str, "Expected yum update"
            assert 'yum install' in yum_str, "Expected yum install"
        
        print("✅ APT and YUM commands generated correctly")
    
    def test_edge_cases(self):
        """Test various edge cases."""
        print("\n10. Testing Edge Cases")
        
        generator = NeuronUpdateScriptGenerator(target_sdk='2.25.0')
        
        # Test package name normalization in target finding
        hyphen_version = generator._find_target_python_version('jax-neuronx')
        underscore_version = generator._find_target_python_version('jax_neuronx')
        assert hyphen_version == underscore_version, "Normalized package names should match"
        
        # Test system package name mapping
        system_name = generator._map_to_system_package_name('aws-neuronx-dkms', 'ubuntu')
        assert system_name == 'aws-neuronx-dkms', "System package name should be preserved"
        
        # Test non-system package
        non_system = generator._map_to_system_package_name('torch-neuronx', 'ubuntu')
        assert non_system is None, "Python package should not map to system package"
        
        print("✅ Edge cases handled correctly")
    
    def test_real_system_scenario(self):
        """Test with real system output from actual AWS Neuron installation."""
        print("\n11. Testing Real System Scenario (Clean SDK 2.25.0)")
        
        # Real system data from user's verbose output
        real_system_packages = {
            'aws-neuronx-collectives': '2.27.34.0',
            'aws-neuronx-dkms': '2.23.9.0',
            'aws-neuronx-oci-hook': '2.11.42.0',
            'aws-neuronx-runtime-lib': '2.27.23.0',
            'aws-neuronx-tools': '2.25.145.0'
        }
        
        real_python_packages = {
            'libneuronxla': '2.2.8201.0',
            'neuronx-cc': '2.20.9961.0',
            'neuronx-distributed': '0.14.18461',
            'neuronx-distributed-training': '1.5.0',
            'torch-neuronx': '2.7.0.2.9.9357'
        }
        
        # This system is already on SDK 2.25.0, so updating to 2.25.0 should show no updates
        generator = NeuronUpdateScriptGenerator(target_sdk='2.25.0')
        
        with patch.object(generator, 'detect_current_packages') as mock_detect:
            mock_detect.return_value = {
                'system_packages': real_system_packages,
                'python_packages': real_python_packages,
                'venv_packages': {},
                'analysis': {}
            }
            
            with patch.object(generator.pkg_mgr_detector, 'detect_package_manager',
                             return_value=('apt', 'ubuntu')):
                
                script = generator.generate_update_script()
                
                # Since system is already on target SDK, should show no updates needed
                assert 'No system packages to update' in script, "Expected no system updates for current SDK"
                assert 'No Python packages to update' in script, "Expected no Python updates for current SDK"
        
        # Test updating this system to a different SDK version (2.24.0)
        generator_224 = NeuronUpdateScriptGenerator(target_sdk='2.24.0')
        
        with patch.object(generator_224, 'detect_current_packages') as mock_detect:
            mock_detect.return_value = {
                'system_packages': real_system_packages,
                'python_packages': real_python_packages,
                'venv_packages': {},
                'analysis': {}
            }
            
            with patch.object(generator_224.pkg_mgr_detector, 'detect_package_manager',
                             return_value=('apt', 'ubuntu')):
                
                script_224 = generator_224.generate_update_script()
                
                # Should generate downgrade commands for packages that differ
                # Note: Some packages might need downgrading from 2.25.0 to 2.24.0
                assert 'SDK version 2.24.0' in script_224, "Expected target SDK 2.24.0 in script"
                assert '#!/bin/bash' in script_224, "Expected bash script format"
        
        print("✅ Real system scenario tested correctly")
    
    def _print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if total - passed > 0:
            print("\nFailed Tests:")
            for test_name, success, error in self.test_results:
                if not success:
                    print(f"  ❌ {test_name}: {error}")
        
        print(f"\n🎯 Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 All tests passed! The update script generator is working correctly.")
        else:
            print("⚠️  Some tests failed. Review and fix the issues.")


def main():
    """Run the test suite."""
    try:
        tester = TestNeuronUpdate()
        tester.run_all_tests()
        return 0
    except Exception as e:
        print(f"❌ Test suite failed to run: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())