"""
AWS Neuron Documentation Scraper

Scrapes package version information from AWS Neuron documentation pages.
"""

import re
import requests
import trafilatura
from typing import Dict, List, Any, Optional
import time


class NeuronDocumentationScraper:
    """Scraper for AWS Neuron SDK documentation."""
    
    CURRENT_RELEASE_URL = "https://awsdocs-neuron.readthedocs-hosted.com/en/latest/release-notes/releasecontent.html"
    PREVIOUS_RELEASES_URL = "https://awsdocs-neuron.readthedocs-hosted.com/en/latest/release-notes/prev/content.html"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; NeuronVersionDetector/1.0)'
        })
    
    def scrape_all_versions(self) -> Dict[str, Any]:
        """Scrape all SDK versions from AWS documentation."""
        print("Scraping current release...")
        current_data = self.scrape_current_release()
        
        print("Scraping previous releases...")
        previous_data = self.scrape_previous_releases()
        
        # Combine data
        all_data = {**current_data, **previous_data}
        
        print(f"Scraped {len(all_data)} SDK versions")
        return all_data
    
    def scrape_current_release(self) -> Dict[str, Any]:
        """Scrape current release information."""
        content = self._fetch_page_content(self.CURRENT_RELEASE_URL)
        return self._parse_release_content(content)
    
    def scrape_previous_releases(self) -> Dict[str, Any]:
        """Scrape previous releases information."""
        content = self._fetch_page_content(self.PREVIOUS_RELEASES_URL)
        return self._parse_release_content(content)
    
    def _fetch_page_content(self, url: str) -> str:
        """Fetch and extract text content from a webpage."""
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                raise Exception(f"Failed to download content from {url}")
            
            text = trafilatura.extract(downloaded)
            if not text:
                raise Exception(f"Failed to extract text from {url}")
            
            return text
        except Exception as e:
            raise Exception(f"Error fetching {url}: {e}")
    
    def _parse_release_content(self, content: str) -> Dict[str, Any]:
        """Parse release content to extract package version information."""
        sdk_versions = {}
        
        # Find all SDK version sections
        version_pattern = r'Neuron (\d+\.\d+\.\d+)'
        version_matches = re.finditer(version_pattern, content)
        
        for match in version_matches:
            version = match.group(1)
            
            # Find the content for this version
            start_pos = match.start()
            
            # Find the next version or end of content
            remaining_content = content[start_pos:]
            next_version_match = re.search(r'Neuron \d+\.\d+\.\d+', remaining_content[len(match.group(0)):])
            
            if next_version_match:
                end_pos = start_pos + len(match.group(0)) + next_version_match.start()
                version_content = content[start_pos:end_pos]
            else:
                version_content = remaining_content
            
            # Parse packages for this version
            packages = self._parse_packages_from_content(version_content)
            
            if packages:
                sdk_versions[version] = packages
                print(f"  Found SDK {version} with {len(packages)} packages")
        
        return sdk_versions
    
    def _parse_packages_from_content(self, content: str) -> Dict[str, Dict[str, str]]:
        """Parse package information from version content."""
        packages = {
            'Trn1': {},
            'Trn2': {},
            'Inf1': {},
            'Inf2': {}
        }
        
        # Look for package sections
        current_platform = None
        
        lines = content.split('\n')
        in_package_list = False
        
        for line in lines:
            line = line.strip()
            
            # Detect platform sections
            if 'Trn1 packages' in line:
                current_platform = 'Trn1'
                in_package_list = False
                continue
            elif 'Trn2 packages' in line:
                current_platform = 'Trn2'
                in_package_list = False
                continue
            elif 'Inf1 packages' in line:
                current_platform = 'Inf1'
                in_package_list = False
                continue
            elif 'Inf2 packages' in line:
                current_platform = 'Inf2'
                in_package_list = False
                continue
            
            # Detect start of package list
            if line.startswith('Component') and 'Package' in line:
                in_package_list = True
                continue
            
            # End of package list
            if in_package_list and (line == '' or line.startswith('Copy to clipboard') or 
                                  line.startswith('Supported Python') or line.startswith('###')):
                in_package_list = False
                continue
            
            # Parse package lines
            if in_package_list and current_platform and line:
                package_match = self._extract_package_info(line)
                if package_match:
                    package_name, version = package_match
                    packages[current_platform][package_name] = version
        
        return packages
    
    def _extract_package_info(self, line: str) -> Optional[tuple]:
        """Extract package name and version from a line."""
        # Skip header lines
        if 'Component' in line or 'Package' in line or line.count(' ') < 2:
            return None
        
        # Split by multiple spaces to separate component from package
        parts = re.split(r'\s{2,}', line)
        if len(parts) >= 2:
            package_spec = parts[-1].strip()
            
            # Extract package name and version
            # Handle different formats: package-version, package_name-version
            # Look for the last dash followed by a version number
            version_match = re.search(r'^(.+)-(\d+(?:\.\d+)*(?:\.\w+)*)$', package_spec)
            if version_match:
                package_name = version_match.group(1)
                version = version_match.group(2)
                return package_name, version
        
        return None


# Test the scraper if run directly
if __name__ == '__main__':
    scraper = NeuronDocumentationScraper()
    data = scraper.scrape_all_versions()
    
    print("\nScraping Results:")
    for sdk_version, platforms in data.items():
        print(f"\nSDK {sdk_version}:")
        for platform, packages in platforms.items():
            if packages:
                print(f"  {platform}: {len(packages)} packages")
                for pkg_name, pkg_version in list(packages.items())[:3]:  # Show first 3
                    print(f"    {pkg_name}: {pkg_version}")
                if len(packages) > 3:
                    print(f"    ... and {len(packages) - 3} more")
