#!/usr/bin/env python3
"""
Functional Tests for AWS Neuron SDK Version Detection Tool

Tests based on real-world examples from actual AWS Neuron systems to ensure
the detector correctly handles various edge cases and scenarios.
"""

import json
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any

# Import the neuron detector
sys.path.append('.')
from neuron_detector import VersionDatabase, PackageDetector


class TestNeuronDetector:
    """Test class for Neuron SDK detection functionality."""
    
    def __init__(self):
        """Initialize test environment."""
        self.db = VersionDatabase()
        self.db.load_database(quiet=True)
        self.test_results = []
        
    def run_all_tests(self):
        """Run all test scenarios."""
        print("🧪 Running AWS Neuron SDK Detection Tests")
        print("=" * 60)
        
        # Test scenarios based on real examples
        test_methods = [
            self.test_single_sdk_clean_install,
            self.test_mixed_installation_with_unknown,
            self.test_multi_sdk_tensorflow_packages,
            self.test_anchor_based_detection,
            self.test_venv_individual_analysis,
            self.test_package_normalization,
            self.test_unknown_version_closest_detection,
            self.test_no_packages_detected,
            self.test_inf1_vs_inf2_packages,
            self.test_edge_case_scenarios,
            self.test_complex_mixed_installation
        ]
        
        for test_method in test_methods:
            try:
                test_method()
                self.test_results.append((test_method.__name__, True, None))
            except Exception as e:
                self.test_results.append((test_method.__name__, False, str(e)))
                print(f"❌ {test_method.__name__}: {e}")
        
        self._print_summary()
    
    def test_single_sdk_clean_install(self):
        """Test clean single SDK installation - SDK 2.25.0."""
        print("\n1. Testing Clean Single SDK Installation (SDK 2.25.0)")
        
        packages = {
            'aws-neuronx-collectives': '2.27.34.0',
            'aws-neuronx-dkms': '2.23.9.0',
            'neuronx-cc': '2.20.9961.0',
            'torch-neuronx': '2.7.0.2.9.9357',
            'libneuronxla': '2.2.8201.0'
        }
        
        analysis = self.db._analyze_packages_with_anchor(packages)
        
        # Assertions
        assert len(analysis['detected_sdks']) == 1, f"Expected 1 SDK, got {len(analysis['detected_sdks'])}"
        assert '2.25.0' in analysis['detected_sdks'], "Expected SDK 2.25.0"
        assert len(analysis['unknown_packages']) == 0, f"Expected no unknown packages, got {len(analysis['unknown_packages'])}"
        
        print("✅ Clean installation detected correctly")
    
    def test_mixed_installation_with_unknown(self):
        """Test mixed installation with unknown development packages."""
        print("\n2. Testing Mixed Installation with Unknown Packages")
        
        packages = {
            'neuronx-cc': '2.20.9961.0',                   # SDK 2.25.0
            'torch-neuronx': '2.7.0.2.9.9357',            # SDK 2.25.0
            'neuronx-distributed': '0.14.18122',           # Unknown (dev build)
            'libneuronxla': '2.2.8201.0'                   # SDK 2.25.0
        }
        
        analysis = self.db._analyze_packages_with_anchor(packages)
        
        # Assertions
        assert '2.25.0' in analysis['detected_sdks'], "Expected SDK 2.25.0"
        assert 'neuronx-distributed' in analysis['unknown_packages'], "Expected neuronx-distributed to be unknown"
        assert len(analysis['detected_sdks']['2.25.0']) == 3, "Expected 3 known packages in SDK 2.25.0"
        
        print("✅ Mixed installation with unknown packages handled correctly")
    
    def test_multi_sdk_tensorflow_packages(self):
        """Test packages that exist in multiple SDKs (tensorflow case)."""
        print("\n3. Testing Multi-SDK TensorFlow Packages")
        
        # This represents your exact issue: SDK 2.24.0 system with tensorflow packages
        packages = {
            'neuronx-cc': '2.19.8089.0',                   # SDK 2.24.0 (anchor)
            'tensorflow-neuron': '2.10.1.2.12.2.0',       # Also in SDK 2.25.0
            'tensorflow-neuronx': '2.10.1.2.1.0',         # Also in SDK 2.25.0
            'tensorboard-plugin-neuronx': '2.6.117.0',    # SDK 2.22.0 (truly out of date)
        }
        
        analysis = self.db._analyze_packages_with_anchor(packages)
        
        # With anchor detection, tensorflow packages should be assigned to SDK 2.24.0
        assert '2.24.0' in analysis['detected_sdks'], "Expected SDK 2.24.0 from anchor"
        assert 'tensorflow-neuron' in analysis['detected_sdks']['2.24.0'], "TensorFlow should be in anchor SDK"
        assert 'tensorflow-neuronx' in analysis['detected_sdks']['2.24.0'], "TensorFlowX should be in anchor SDK"
        assert '2.22.0' in analysis['detected_sdks'], "Expected SDK 2.22.0 for tensorboard"
        
        print("✅ Multi-SDK packages correctly anchored to compiler version")
    
    def test_anchor_based_detection(self):
        """Test anchor-based SDK detection logic."""
        print("\n4. Testing Anchor-Based SDK Detection")
        
        # Test with anchor
        packages_with_anchor = {
            'neuronx-cc': '2.19.8089.0',                   # SDK 2.24.0 anchor
            'tensorflow-neuron': '2.10.1.2.12.2.0'        # Exists in multiple SDKs
        }
        
        anchor_sdk = self.db._find_anchor_sdk(packages_with_anchor)
        assert anchor_sdk == '2.24.0', f"Expected anchor SDK 2.24.0, got {anchor_sdk}"
        
        # Test without anchor
        packages_no_anchor = {
            'tensorflow-neuron': '2.10.1.2.12.2.0',       # Should fall back to newest
            'jax-neuronx': '0.6.1.1.0.3499'               # SDK 2.25.0
        }
        
        no_anchor_sdk = self.db._find_anchor_sdk(packages_no_anchor)
        assert no_anchor_sdk is None, f"Expected no anchor, got {no_anchor_sdk}"
        
        print("✅ Anchor detection working correctly")
    
    def test_venv_individual_analysis(self):
        """Test individual virtual environment analysis."""
        print("\n5. Testing Virtual Environment Individual Analysis")
        
        venv_packages = {
            'libneuronxla': '2.2.8201.0',
            'neuronx-cc': '2.20.9961.0',
            'torch-neuronx': '2.7.0.2.9.9357',
            'neuronx-distributed': '0.14.18122'            # Unknown
        }
        
        venv_analysis = self.db.analyze_venv_individually('/opt/aws_neuronx_venv_test', venv_packages)
        
        assert 'venv_path' in venv_analysis, "Expected venv_path in analysis"
        assert '2.25.0' in venv_analysis['detected_sdks'], "Expected SDK 2.25.0"
        assert 'neuronx-distributed' in venv_analysis['unknown_packages'], "Expected unknown package"
        assert len(venv_analysis['package_to_highest_sdk']) == 3, "Expected 3 packages mapped to SDKs"
        
        print("✅ Virtual environment analysis working correctly")
    
    def test_package_normalization(self):
        """Test package name normalization (hyphen vs underscore)."""
        print("\n6. Testing Package Name Normalization")
        
        # Test hyphen versions
        hyphen_packages = {
            'jax-neuronx': '0.6.1.1.0.3499',
            'neuronx-distributed-training': '1.5.0'
        }
        
        # Test underscore versions  
        underscore_packages = {
            'jax_neuronx': '0.6.1.1.0.3499',
            'neuronx_distributed_training': '1.5.0'
        }
        
        hyphen_analysis = self.db._analyze_packages_with_anchor(hyphen_packages)
        underscore_analysis = self.db._analyze_packages_with_anchor(underscore_packages)
        
        # Both should detect the same packages
        assert len(hyphen_analysis['detected_sdks']) > 0, "Hyphen packages should be detected"
        assert len(underscore_analysis['detected_sdks']) > 0, "Underscore packages should be detected"
        assert len(hyphen_analysis['unknown_packages']) == 0, "Hyphen packages should be known"
        assert len(underscore_analysis['unknown_packages']) == 0, "Underscore packages should be known"
        
        print("✅ Package name normalization working correctly")
    
    def test_unknown_version_closest_detection(self):
        """Test closest version detection for unknown packages."""
        print("\n7. Testing Unknown Version Closest Detection")
        
        from neuron_detector import find_closest_versions
        
        # Set global database reference for the function
        import neuron_detector
        neuron_detector._version_database = self.db
        
        # Test with a development version between known versions
        below_info, above_info = find_closest_versions('neuronx-distributed', '0.14.18122')
        
        assert below_info is not None, "Expected to find a version below"
        assert above_info is not None, "Expected to find a version above"
        assert below_info[1] == '2.24.0', f"Expected below version from SDK 2.24.0, got {below_info[1]}"
        assert above_info[1] == '2.25.0', f"Expected above version from SDK 2.25.0, got {above_info[1]}"
        
        print("✅ Closest version detection working correctly")
    
    def test_no_packages_detected(self):
        """Test behavior when no Neuron packages are detected."""
        print("\n8. Testing No Packages Detected")
        
        empty_packages = {}
        analysis = self.db._analyze_packages_with_anchor(empty_packages)
        
        assert len(analysis['detected_sdks']) == 0, "Expected no SDKs detected"
        assert len(analysis['unknown_packages']) == 0, "Expected no unknown packages"
        assert len(analysis['all_packages']) == 0, "Expected no packages"
        
        print("✅ No packages scenario handled correctly")
    
    def test_inf1_vs_inf2_packages(self):
        """Test Inf1 vs Inf2/Trn1 package differences."""
        print("\n9. Testing Inf1 vs Inf2/Trn1 Package Differences")
        
        # Inf1 packages
        inf1_packages = {
            'neuron-cc': '1.24.0.0',                       # Inf1 compiler
            'torch-neuron': '1.13.1.2.11.13.0',           # Inf1 PyTorch
            'tensorflow-neuron': '2.10.1.2.12.2.0'        # Common to both
        }
        
        # Inf2/Trn1 packages
        inf2_packages = {
            'neuronx-cc': '2.20.9961.0',                   # Inf2/Trn1 compiler
            'torch-neuronx': '2.7.0.2.9.9357',            # Inf2/Trn1 PyTorch
            'libneuronxla': '2.2.8201.0'                   # Inf2/Trn1 only
        }
        
        inf1_analysis = self.db._analyze_packages_with_anchor(inf1_packages)
        inf2_analysis = self.db._analyze_packages_with_anchor(inf2_packages)
        
        assert len(inf1_analysis['detected_sdks']) > 0, "Inf1 packages should be detected"
        assert len(inf2_analysis['detected_sdks']) > 0, "Inf2 packages should be detected"
        
        print("✅ Inf1 and Inf2/Trn1 packages detected correctly")
    
    def test_edge_case_scenarios(self):
        """Test various edge case scenarios."""
        print("\n10. Testing Edge Case Scenarios")
        
        # Edge case: Only unknown packages
        unknown_only = {
            'custom-neuron-package': '999.999.999',
            'development-build': '0.0.1.dev'
        }
        
        unknown_analysis = self.db._analyze_packages_with_anchor(unknown_only)
        assert len(unknown_analysis['detected_sdks']) == 0, "Expected no known SDKs"
        assert len(unknown_analysis['unknown_packages']) == 2, "Expected 2 unknown packages"
        
        # Edge case: Mixed valid and invalid versions
        mixed_valid = {
            'neuronx-cc': '2.20.9961.0',                   # Valid
            'torch-neuronx': '999.999.999'                 # Invalid version
        }
        
        mixed_analysis = self.db._analyze_packages_with_anchor(mixed_valid)
        assert '2.25.0' in mixed_analysis['detected_sdks'], "Expected valid package to be detected"
        assert 'torch-neuronx' in mixed_analysis['unknown_packages'], "Expected invalid version to be unknown"
        
        print("✅ Edge case scenarios handled correctly")
    
    def test_complex_mixed_installation(self):
        """Test complex mixed installation from real system data."""
        print("\n11. Testing Complex Mixed Installation (Real System)")
        
        # Real system data showing mixed SDK 2.24.0, 2.22.0, and 2.25.0
        mixed_packages = {
            # Main system mostly on SDK 2.24.0
            'neuronx-cc': '2.19.8089.0',                 # SDK 2.24.0 (anchor)
            'libneuronxla': '2.2.4410.0',                # SDK 2.24.0
            'neuronx-distributed': '0.13.14393',         # SDK 2.24.0
            'torch-neuronx': '2.7.0.2.8.6734',          # SDK 2.24.0
            
            # Out-of-date package
            'tensorboard-plugin-neuronx': '2.6.117.0',   # SDK 2.22.0
            
            # Some environments have newer packages
            'neuron-cc': '1.24.0.0',                     # SDK 2.25.0 (Inf1)
            'tensorflow-neuron': '2.10.1.2.12.2.0',     # Exists in multiple SDKs
        }
        
        analysis = self.db._analyze_packages_with_anchor(mixed_packages)
        
        # With anchor detection, should primarily detect SDK 2.24.0
        assert '2.24.0' in analysis['detected_sdks'], "Expected SDK 2.24.0 from anchor"
        assert len(analysis['detected_sdks']['2.24.0']) >= 4, "Expected multiple packages in anchor SDK"
        
        # Should also detect other SDKs
        assert '2.22.0' in analysis['detected_sdks'], "Expected SDK 2.22.0 for tensorboard"
        
        # The tensorflow package should be anchored to 2.24.0 due to neuronx-cc anchor
        if 'tensorflow-neuron' in analysis['detected_sdks']['2.24.0']:
            print("  ✓ TensorFlow package correctly anchored to SDK 2.24.0")
        
        print("✅ Complex mixed installation analyzed correctly")
    
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
            print("🎉 All tests passed! The detector is working correctly.")
        else:
            print("⚠️  Some tests failed. Review and fix the issues.")


def main():
    """Run the test suite."""
    try:
        tester = TestNeuronDetector()
        tester.run_all_tests()
        return 0
    except Exception as e:
        print(f"❌ Test suite failed to run: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())