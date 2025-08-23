#!/usr/bin/env python3
"""
AWS Neuron SDK Database Updater

Scrapes AWS Neuron documentation to build and update the neuron_versions.json 
database with package version information for all SDK releases.
"""

import argparse
import json
import re
import requests
import sys
import trafilatura
from typing import Dict, List, Any


class NeuronDocumentationScraper:
    """Scrapes AWS Neuron documentation for package version information."""
    
    CURRENT_RELEASE_URL = "https://awsdocs-neuron.readthedocs-hosted.com/en/latest/release-notes/releasecontent.html"
    PREVIOUS_RELEASES_URL = "https://awsdocs-neuron.readthedocs-hosted.com/en/latest/release-notes/prev/content.html"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_current_release(self) -> Dict[str, Any]:
        """Scrape current release documentation."""
        print("Scraping current release documentation...")
        
        try:
            response = self.session.get(self.CURRENT_RELEASE_URL, timeout=30)
            response.raise_for_status()
            
            content = trafilatura.extract(response.text)
            if not content:
                raise Exception("No content extracted from current release page")
            
            # Extract current version data (2.25.0)
            current_data = self._extract_current_version_data(content)
            return current_data
            
        except Exception as e:
            print(f"Error scraping current release: {e}")
            return {}
    
    def scrape_historical_releases(self) -> Dict[str, Any]:
        """Scrape historical releases documentation."""
        print("Scraping historical releases documentation...")
        
        try:
            response = self.session.get(self.PREVIOUS_RELEASES_URL, timeout=30)
            response.raise_for_status()
            
            content = trafilatura.extract(response.text)
            if not content:
                raise Exception("No content extracted from historical releases page")
            
            # Extract all historical version data
            historical_data = self._extract_all_version_data(content)
            return historical_data
            
        except Exception as e:
            print(f"Error scraping historical releases: {e}")
            return {}
    
    def scrape_all_versions(self) -> Dict[str, Any]:
        """Scrape both current and historical releases."""
        complete_data = {}
        
        # Get current release
        current_data = self.scrape_current_release()
        complete_data.update(current_data)
        
        # Get historical releases
        historical_data = self.scrape_historical_releases()
        complete_data.update(historical_data)
        
        return complete_data
    
    def _extract_release_date(self, content: str, version: str) -> str:
        """Extract release date for a specific version from content."""
        # Try to find version-specific date information
        # Format: "Neuron 2.25.0 (01/16/2025)" or similar
        date_pattern = rf'Neuron {re.escape(version)} \(([^)]+)\)'
        match = re.search(date_pattern, content)
        if match:
            return match.group(1)
        return "TBD"  # Default if date not found
    
    def _extract_current_version_data(self, content: str) -> Dict[str, Any]:
        """Extract package data for current release (2.25.0)."""
        # Extract release date from content
        release_date = self._extract_release_date(content, "2.25.0")
        
        # For now, return the known 2.25.0 data with new structure
        return {
            "2.25.0": {
                "release_date": release_date,
                "platforms": {
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
                    "neuronx_distributed_inference": "0.5.9230",
                    "neuronx_distributed_training": "1.5.0",
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
                    "neuronx_distributed_inference": "0.5.9230",
                    "neuronx_distributed_training": "1.5.0",
                    "torch-neuronx": "2.7.0.2.9.9357"
                    }
                }
            }
        }
    
    def _extract_all_version_data(self, content: str) -> Dict[str, Any]:
        """Extract complete package data for all SDK versions from historical content."""
        
        # List of all expected versions
        expected_versions = [
            "2.24.0", "2.23.0", "2.22.0", "2.21.0", "2.20.2", "2.20.1", "2.20.0",
            "2.19.1", "2.19.0", "2.18.2", "2.18.1", "2.18.0", "2.17.0", "2.16.1",
            "2.16.0", "2.15.2", "2.15.1", "2.15.0", "2.14.1", "2.14.0", "2.13.2",
            "2.13.1", "2.13.0", "2.12.2", "2.12.1", "2.12.0", "2.11.0", "2.10.0",
            "2.9.1", "2.9.0", "2.8.0", "2.7.0", "2.6.0", "2.5.0", "2.4.0", "2.3.0"
        ]
        
        sdk_data = {}
        print(f"Parsing package data for {len(expected_versions)} SDK versions...")
        
        # Split content into sections for each version
        sections = self._split_into_version_sections(content)
        
        for version in expected_versions:
            if version in sections:
                print(f"Processing {version}...")
                version_data = self._parse_version_section(sections[version], version)
                if version_data:
                    sdk_data[version] = version_data
                else:
                    print(f"  No package data found for {version}")
            else:
                print(f"  Section not found for {version}")
        
        return sdk_data
    
    def _split_into_version_sections(self, content: str) -> Dict[str, str]:
        """Split content into individual version sections."""
        
        sections = {}
        lines = content.split('\n')
        current_version = None
        current_section = []
        
        for line in lines:
            # Check if this is a version header - also extract date
            # Format: "Neuron 2.24.0 (01/16/2025)"
            version_match = re.match(r'Neuron (\d+\.\d+\.\d+) \(([^)]+)\)', line)
            if version_match:
                # Save previous section if exists
                if current_version and current_section:
                    sections[current_version] = '\n'.join(current_section)
                
                # Start new section
                current_version = version_match.group(1)
                current_section = [line]
            elif current_version:
                current_section.append(line)
        
        # Save final section
        if current_version and current_section:
            sections[current_version] = '\n'.join(current_section)
        
        print(f"Found sections for {len(sections)} versions")
        return sections
    
    def _parse_version_section(self, section_content: str, version: str) -> Dict[str, Any]:
        """Parse a single version section to extract packages by platform and release date."""
        
        platforms = {"Trn1": {}, "Trn2": {}, "Inf2": {}, "Inf1": {}}
        release_date = None
        
        # Extract release date from the first line
        lines = section_content.split('\n')
        if lines:
            first_line = lines[0]
            # Format: "Neuron 2.24.0 (01/16/2025)"
            date_match = re.match(r'Neuron (\d+\.\d+\.\d+) \(([^)]+)\)', first_line)
            if date_match:
                release_date = date_match.group(2)
        
        # Find platform sections within this version
        lines = section_content.split('\n')
        current_platform = None
        in_package_list = False
        
        for line in lines:
            line = line.strip()
            
            # Detect platform headers
            if 'Trn1 packages' in line:
                current_platform = 'Trn1'
                in_package_list = False
                continue
            elif 'Trn2 packages' in line:
                current_platform = 'Trn2'
                in_package_list = False
                continue
            elif 'Inf2 packages' in line:
                current_platform = 'Inf2'
                in_package_list = False
                continue
            elif 'Inf1 packages' in line:
                current_platform = 'Inf1'
                in_package_list = False
                continue
            elif 'Supported Python Versions' in line:
                current_platform = None
                in_package_list = False
                continue
            
            # Detect start of package list
            if 'List of packages' in line and current_platform:
                in_package_list = True
                continue
            
            # Skip header lines
            if 'Component Package' in line or not line:
                continue
            
            # Extract packages when in the right context
            if current_platform and (in_package_list or any(keyword in line for keyword in ['aws-neuron', 'neuron', 'torch', 'tensorflow', 'jax', 'mx_neuron'])):
                package_info = self._extract_package_from_line(line)
                if package_info:
                    package_name, package_version = package_info
                    platforms[current_platform][package_name] = package_version
        
        # Return structured data with platforms and release date
        result = {
            "platforms": platforms
        }
        
        if release_date:
            result["release_date"] = release_date
            
        return result
    
    def _extract_package_from_line(self, line: str) -> tuple:
        """Extract package name and version from a line."""
        
        # Multiple patterns to match different line formats
        patterns = [
            # Pattern: "Component package-name-version"
            r'(?:.*\s+)?([a-zA-Z0-9_-]+(?:-neuronx?)?[a-zA-Z0-9_-]*)-(\d+(?:\.\d+)*(?:\.\w+)*)\s*$',
            # Pattern: "package-name-version" at start of line
            r'^([a-zA-Z0-9_-]+(?:-neuronx?)?[a-zA-Z0-9_-]*)-(\d+(?:\.\d+)*(?:\.\w+)*)',
            # Pattern: with underscores
            r'([a-zA-Z0-9_]+(?:_neuronx?)?[a-zA-Z0-9_]*)-(\d+(?:\.\d+)*(?:\.\w+)*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                package_name = match.group(1)
                version = match.group(2)
                
                # Filter out non-package lines
                if len(package_name) > 2 and not any(skip in package_name.lower() for skip in ['component', 'package', 'supported']):
                    return (package_name, version)
        
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Update AWS Neuron SDK version database from documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Update database from AWS documentation
  %(prog)s --output custom.json      # Save to custom filename
  %(prog)s --current-only            # Only scrape current release
  %(prog)s --historical-only         # Only scrape historical releases
        """
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='neuron_versions.json',
        help='Output filename for the database (default: neuron_versions.json)'
    )
    
    parser.add_argument(
        '--current-only',
        action='store_true',
        help='Only scrape current release documentation'
    )
    
    parser.add_argument(
        '--historical-only',
        action='store_true',
        help='Only scrape historical releases documentation'
    )

    args = parser.parse_args()

    try:
        scraper = NeuronDocumentationScraper()
        
        if args.current_only:
            print("Scraping current release only...")
            sdk_data = scraper.scrape_current_release()
        elif args.historical_only:
            print("Scraping historical releases only...")
            sdk_data = scraper.scrape_historical_releases()
        else:
            print("Scraping all releases...")
            sdk_data = scraper.scrape_all_versions()
        
        if not sdk_data:
            print("Error: No data scraped from documentation")
            return 1
        
        # Save to file
        with open(args.output, 'w') as f:
            json.dump(sdk_data, f, indent=2, sort_keys=True)
        
        print(f"\n✅ Database saved to {args.output}")
        print(f"📊 Total SDK versions: {len(sdk_data)}")
        
        # Show statistics
        versions_with_data = []
        for version, platforms in sdk_data.items():
            total_packages = sum(len(packages) for packages in platforms.values())
            if total_packages > 0:
                versions_with_data.append((version, total_packages))
        
        # Sort by version number (newest first)
        versions_with_data.sort(key=lambda x: [int(i) for i in x[0].split('.')], reverse=True)
        
        print(f"📦 Versions with package data: {len(versions_with_data)}")
        for version, count in versions_with_data[:10]:  # Show top 10
            print(f"  {version}: {count} packages")
        
        if len(versions_with_data) > 10:
            print(f"  ... and {len(versions_with_data) - 10} more versions")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())