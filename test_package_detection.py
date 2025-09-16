#!/usr/bin/env python3
"""
Test package detection with example data to prevent regressions.
Ensures the detector properly handles both 'ii' and 'hi' package status.
"""

import unittest
from unittest.mock import patch, MagicMock
import subprocess
import sys
import os
import io

# Add current directory to path to import neuron_detector
sys.path.insert(0, os.path.dirname(__file__))

from neuron_detector import PackageDetector, print_verbose_output


class TestPackageDetection(unittest.TestCase):
    """Test package detection with realistic example data."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = PackageDetector()
        
        # Example dpkg -l output with both 'ii' and 'hi' status packages
        self.sample_dpkg_output = """Desired=Unknown/Install/Remove/Purge/Hold
| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend
|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)
||/ Name                                Version                             Architecture Description
+++-===================================-===================================-============-===============================================================================
ii  adduser                             3.118ubuntu2                        all          add and remove users and groups
hi  aws-neuronx-collectives             2.27.34.0-ec8cd5e8b                 amd64        neuron_ccom built using CMake
hi  aws-neuronx-dkms                    2.23.9.0                            all          aws-neuronx driver in DKMS format.
hi  aws-neuronx-oci-hook                2.11.42.0                           amd64        neuron_oci_hook built using CMake
hi  aws-neuronx-runtime-lib             2.27.23.0-8deec4dbf                 amd64        neuron_runtime built using CMake
hi  aws-neuronx-tools                   2.25.145.0                          amd64        Neuron profile and debug tools
ii  base-files                          11.1ubuntu2.2                       amd64        Debian base system miscellaneous files
ii  neuron-example-pkg                  1.0.0                               amd64        Example neuron package with ii status"""

        # Example pip list output
        self.sample_pip_output = """Package               Version
--------------------- -----------
libneuronxla          2.2.8201.0
neuronx-cc            2.20.9961.0
neuronx-distributed   0.14.18461
torch-neuronx         2.7.0.2.9.9357
transformers-neuronx  0.13.1216
pip                   21.2.4
setuptools            58.1.0"""

        # Expected parsed packages
        self.expected_system_packages = {
            'aws-neuronx-collectives': '2.27.34.0',
            'aws-neuronx-dkms': '2.23.9.0', 
            'aws-neuronx-oci-hook': '2.11.42.0',
            'aws-neuronx-runtime-lib': '2.27.23.0',
            'aws-neuronx-tools': '2.25.145.0',
            'neuron-example-pkg': '1.0.0'
        }

        self.expected_python_packages = {
            'libneuronxla': '2.2.8201.0',
            'neuronx-cc': '2.20.9961.0',
            'neuronx-distributed': '0.14.18461',
            'torch-neuronx': '2.7.0.2.9.9357',
            'transformers-neuronx': '0.13.1216'
        }

    def test_dpkg_parsing_with_hi_status(self):
        """Test that dpkg parsing handles both 'ii' and 'hi' status packages."""
        # Mock subprocess to fail apt first, then succeed with dpkg
        def mock_subprocess(*args, **kwargs):
            if 'apt' in args[0]:
                # Fail apt to force fallback to dpkg
                raise subprocess.CalledProcessError(1, args[0])
            elif 'dpkg' in args[0]:
                # Return sample dpkg output
                result = MagicMock()
                result.stdout = self.sample_dpkg_output
                result.returncode = 0
                return result
            else:
                raise FileNotFoundError()
        
        with patch('subprocess.run', side_effect=mock_subprocess):
            # Test get_system_packages
            packages = self.detector.get_system_packages()
            
            # Verify all expected packages were found
            self.assertEqual(packages, self.expected_system_packages)
            
            # Verify both 'ii' and 'hi' status packages are included
            self.assertIn('aws-neuronx-collectives', packages)  # hi status
            self.assertIn('neuron-example-pkg', packages)       # ii status

    def test_pip_parsing(self):
        """Test that pip parsing works correctly."""
        def mock_subprocess(*args, **kwargs):
            if 'pip' in args[0] or (isinstance(args[0], list) and len(args[0]) > 1 and 'pip' in args[0][1]):
                result = MagicMock()
                result.stdout = self.sample_pip_output
                result.returncode = 0
                return result
            else:
                raise FileNotFoundError()
        
        with patch('subprocess.run', side_effect=mock_subprocess):
            # Test get_python_packages
            packages = self.detector.get_python_packages()
            
            # Verify all expected packages were found
            self.assertEqual(packages, self.expected_python_packages)

    def test_verbose_output_displays_system_packages(self):
        """Test that verbose output properly displays system packages."""
        # Mock the analysis result
        mock_analysis = {
            'detected_sdks': {'2.25.0': self.expected_system_packages},
            'unknown_packages': {},
            'mixed_installation': False,
            'assessment': 'Complete SDK installation detected'
        }
        
        # Capture stdout to verify verbose output
        captured_output = io.StringIO()
        
        with patch('sys.stdout', captured_output):
            print_verbose_output(
                analysis=mock_analysis,
                system_packages=self.expected_system_packages,
                current_python_packages=self.expected_python_packages,
                venv_packages={},
                venv_analyses=None
            )
        
        output = captured_output.getvalue()
        
        # Verify system packages section is displayed
        self.assertIn("System Packages (dpkg):", output)
        self.assertIn("aws-neuronx-collectives: 2.27.34.0", output)
        self.assertIn("aws-neuronx-dkms: 2.23.9.0", output)
        self.assertIn("aws-neuronx-tools: 2.25.145.0", output)
        
        # Verify Python packages section is displayed
        self.assertIn("Python Packages (current environment):", output)
        self.assertIn("neuronx-cc: 2.20.9961.0", output)
        self.assertIn("torch-neuronx: 2.7.0.2.9.9357", output)

    def test_dpkg_line_parsing_edge_cases(self):
        """Test edge cases in dpkg line parsing."""
        # Test 'hi' status parsing specifically
        hi_line = "hi  aws-neuronx-collectives             2.27.34.0-ec8cd5e8b                 amd64        neuron_ccom built using CMake"
        self.assertTrue(self.detector._is_neuron_package_line_dpkg(hi_line))
        parsed = self.detector._parse_dpkg_line(hi_line)
        self.assertEqual(parsed, ('aws-neuronx-collectives', '2.27.34.0-ec8cd5e8b'))
        
        # Test 'ii' status parsing
        ii_line = "ii  neuron-example-pkg                  1.0.0                               amd64        Example neuron package"
        self.assertTrue(self.detector._is_neuron_package_line_dpkg(ii_line))
        parsed = self.detector._parse_dpkg_line(ii_line)
        self.assertEqual(parsed, ('neuron-example-pkg', '1.0.0'))
        
        # Test non-neuron package is ignored
        other_line = "ii  adduser                             3.118ubuntu2                        all          add and remove users"
        self.assertFalse(self.detector._is_neuron_package_line_dpkg(other_line))
        
        # Test invalid status is ignored
        invalid_status = "rc  aws-neuronx-old-pkg                1.0.0                               amd64        removed package"
        parsed = self.detector._parse_dpkg_line(invalid_status)
        self.assertIsNone(parsed)

    def test_full_detection_workflow(self):
        """Test the complete detection workflow with mocked system calls."""
        def mock_subprocess(*args, **kwargs):
            if 'apt' in args[0]:
                # Fail apt to force dpkg fallback
                raise subprocess.CalledProcessError(1, args[0])
            elif 'dpkg' in args[0]:
                result = MagicMock()
                result.stdout = self.sample_dpkg_output
                result.returncode = 0
                return result
            elif 'pip' in args[0] or (isinstance(args[0], list) and len(args[0]) > 1 and 'pip' in args[0][1]):
                result = MagicMock()
                result.stdout = self.sample_pip_output
                result.returncode = 0
                return result
            else:
                raise FileNotFoundError()
        
        with patch('subprocess.run', side_effect=mock_subprocess):
            # Test complete detection
            system_packages = self.detector.get_system_packages()
            python_packages = self.detector.get_python_packages()
            
            # Verify packages were detected
            self.assertEqual(len(system_packages), 6)  # 5 aws-neuronx + 1 neuron-example
            self.assertEqual(len(python_packages), 5)
            
            # Verify specific held packages are found
            self.assertIn('aws-neuronx-collectives', system_packages)
            self.assertIn('aws-neuronx-dkms', system_packages)

    def test_version_cleaning(self):
        """Test that version strings are properly cleaned."""
        # Test build suffix removal
        version_with_suffix = "2.27.34.0-ec8cd5e8b"
        cleaned = self.detector._clean_version(version_with_suffix)
        self.assertEqual(cleaned, "2.27.34.0")
        
        # Test already clean version
        clean_version = "2.23.9.0"
        cleaned = self.detector._clean_version(clean_version)
        self.assertEqual(cleaned, "2.23.9.0")


def run_tests():
    """Run the test suite."""
    print("Running package detection tests...")
    unittest.main(verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()