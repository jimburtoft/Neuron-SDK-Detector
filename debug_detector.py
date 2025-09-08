#!/usr/bin/env python3
"""
Comprehensive debug script to identify why system packages aren't showing up.
Run this on your actual system where the neuron packages are installed.
"""

import subprocess
import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))
from neuron_detector import PackageDetector

def test_apt_parsing():
    """Test apt parsing with actual system data."""
    print("=== TESTING APT PARSING ===")
    detector = PackageDetector()
    
    try:
        result = subprocess.run(
            ['apt', 'list', '--installed'],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"✓ apt list succeeded, {len(result.stdout.splitlines())} total lines")
        
        neuron_lines = []
        parsed_packages = {}
        
        for line_num, line in enumerate(result.stdout.splitlines(), 1):
            if detector._is_neuron_package_line_apt(line):
                neuron_lines.append(line)
                print(f"\n📦 Line {line_num}: {repr(line)}")
                
                # Test parsing this specific line
                try:
                    parsed = detector._parse_apt_line(line)
                    if parsed:
                        name, version = parsed
                        parsed_packages[name] = version
                        print(f"   ✓ PARSED: name='{name}', version='{version}'")
                    else:
                        print(f"   ❌ PARSE FAILED: returned None")
                        
                        # Debug the parsing step by step
                        print(f"   🔍 Debug parsing:")
                        if '/' in line:
                            parts = line.split('/')
                            print(f"      Split by '/': {parts}")
                            if len(parts) >= 2:
                                name = parts[0].strip()
                                repo_status_version_part = parts[1]
                                print(f"      Name: '{name}'")
                                print(f"      After '/': '{repo_status_version_part}'")
                                
                                if ',' in repo_status_version_part:
                                    status_version_part = repo_status_version_part.split(',', 1)[1].strip()
                                    print(f"      After comma: '{status_version_part}'")
                                else:
                                    status_version_part = repo_status_version_part.strip()
                                    print(f"      No comma, using: '{status_version_part}'")
                                
                                parts_after_slash = status_version_part.split()
                                print(f"      Split by space: {parts_after_slash}")
                                
                                for i, part in enumerate(parts_after_slash):
                                    has_dot = '.' in part
                                    has_digit = any(c.isdigit() for c in part)
                                    print(f"        Part {i}: '{part}' - dot:{has_dot}, digit:{has_digit}")
                        
                except Exception as e:
                    print(f"   💥 EXCEPTION in parsing: {e}")
                    traceback.print_exc()
        
        print(f"\nAPT SUMMARY:")
        print(f"  Found {len(neuron_lines)} neuron lines")
        print(f"  Successfully parsed {len(parsed_packages)} packages")
        if parsed_packages:
            for name, version in parsed_packages.items():
                print(f"    {name}: {version}")
        
        return parsed_packages
        
    except Exception as e:
        print(f"❌ apt list failed: {e}")
        return {}

def test_dpkg_parsing():
    """Test dpkg parsing with actual system data."""
    print("\n=== TESTING DPKG PARSING ===")
    detector = PackageDetector()
    
    try:
        result = subprocess.run(
            ['dpkg', '-l'],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"✓ dpkg succeeded, {len(result.stdout.splitlines())} total lines")
        
        neuron_lines = []
        parsed_packages = {}
        
        for line_num, line in enumerate(result.stdout.splitlines(), 1):
            if detector._is_neuron_package_line_dpkg(line):
                neuron_lines.append(line)
                print(f"\n📦 Line {line_num}: {repr(line)}")
                
                try:
                    parsed = detector._parse_dpkg_line(line)
                    if parsed:
                        name, version = parsed
                        parsed_packages[name] = version
                        print(f"   ✓ PARSED: name='{name}', version='{version}'")
                    else:
                        print(f"   ❌ PARSE FAILED: returned None")
                except Exception as e:
                    print(f"   💥 EXCEPTION in parsing: {e}")
        
        print(f"\nDPKG SUMMARY:")
        print(f"  Found {len(neuron_lines)} neuron lines")
        print(f"  Successfully parsed {len(parsed_packages)} packages")
        if parsed_packages:
            for name, version in parsed_packages.items():
                print(f"    {name}: {version}")
        
        return parsed_packages
        
    except Exception as e:
        print(f"❌ dpkg failed: {e}")
        return {}

def test_get_system_packages():
    """Test the actual get_system_packages method with detailed debugging."""
    print("\n=== TESTING get_system_packages() METHOD ===")
    detector = PackageDetector()
    
    # Monkey patch to add debug output
    original_run = subprocess.run
    call_count = 0
    
    def debug_subprocess_run(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        cmd = args[0] if args else kwargs.get('args', 'unknown')
        print(f"\n🔧 Subprocess call #{call_count}: {cmd}")
        
        try:
            result = original_run(*args, **kwargs)
            print(f"   ✓ SUCCESS: returncode={result.returncode}, stdout_lines={len(result.stdout.splitlines())}")
            return result
        except subprocess.CalledProcessError as e:
            print(f"   ❌ CalledProcessError: returncode={e.returncode}")
            raise
        except FileNotFoundError as e:
            print(f"   ❌ FileNotFoundError: {e}")
            raise
        except Exception as e:
            print(f"   💥 Exception: {e}")
            raise
    
    # Apply the patch
    subprocess.run = debug_subprocess_run
    
    try:
        print("Calling detector.get_system_packages()...")
        packages = detector.get_system_packages()
        print(f"\n🎯 FINAL RESULT: {len(packages)} packages")
        
        if packages:
            for name, version in packages.items():
                print(f"  ✓ {name}: {version}")
        else:
            print("  ❌ NO PACKAGES RETURNED")
        
        return packages
        
    except Exception as e:
        print(f"💥 EXCEPTION in get_system_packages(): {e}")
        traceback.print_exc()
        return {}
    finally:
        # Restore original
        subprocess.run = original_run

def test_version_cleaning():
    """Test version cleaning with your actual versions."""
    print("\n=== TESTING VERSION CLEANING ===")
    detector = PackageDetector()
    
    test_versions = [
        '2.27.34.0-ec8cd5e8b',
        '2.23.9.0', 
        '2.11.42.0',
        '2.27.23.0-8deec4dbf',
        '2.25.145.0'
    ]
    
    for version in test_versions:
        cleaned = detector._clean_version(version)
        print(f"  '{version}' → '{cleaned}'")

def main():
    print("🔍 COMPREHENSIVE NEURON DETECTOR DEBUG")
    print("="*50)
    
    # Test individual components
    apt_packages = test_apt_parsing()
    dpkg_packages = test_dpkg_parsing()
    
    # Test version cleaning
    test_version_cleaning()
    
    # Test the actual method
    actual_packages = test_get_system_packages()
    
    # Summary comparison
    print("\n" + "="*50)
    print("📊 FINAL COMPARISON:")
    print(f"  APT found & parsed: {len(apt_packages)} packages")
    print(f"  DPKG found & parsed: {len(dpkg_packages)} packages")
    print(f"  get_system_packages() returned: {len(actual_packages)} packages")
    
    if len(actual_packages) == 0 and (len(apt_packages) > 0 or len(dpkg_packages) > 0):
        print("\n🚨 PROBLEM IDENTIFIED:")
        print("   Individual parsing works but get_system_packages() returns 0!")
        print("   This suggests an issue in the method's control flow.")
    elif len(actual_packages) > 0:
        print(f"\n✅ SUCCESS: get_system_packages() is working correctly!")
    else:
        print(f"\n❓ NO PACKAGES FOUND: Check if neuron packages are actually installed")

if __name__ == '__main__':
    main()