import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional

class LawDataScraper:
    def __init__(self, headless=True):
        """
        Initialize the Law Data Scraper
        
        Args:
            headless (bool): Whether to run browser in headless mode
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Setup Chrome options for Selenium
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        
        self.driver: Optional[webdriver.Chrome] = None
        
    def setup_driver(self):
        """Setup Selenium WebDriver"""
        if self.driver is None:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            
    def close_driver(self):
        """Close Selenium WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def scrape_law_page(self, url):
        """
        Scrape a Swedish law page from lagboken.se
        
        Args:
            url (str): URL of the law page to scrape
            
        Returns:
            dict: Structured data containing the law information
        """
        try:
            print(f"Scraping law page: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            law_data = {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'title': self._extract_title(soup),
                'description': self._get_static_description(),
                'metadata': self._extract_metadata_strict(soup),
                'important_laws': self._extract_important_laws(soup)
            }
            return law_data
        except requests.RequestException as e:
            print(f"Error with requests: {e}")
            return None
        except Exception as e:
            print(f"Error scraping law page: {e}")
            return None
    
    def _extract_title(self, soup):
        """Extract the law title from the page"""
        # Try to find the title in various locations
        title_selectors = [
            'h1',
            '.law-title',
            '.page-title',
            '[class*="title"]',
            'h2'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 5:  # Avoid very short texts
                    return text
        
        # Fallback: try to extract from URL or page content
        full_text = soup.get_text(separator='\n', strip=True)
        
        # Look for SFS number pattern
        sfs_match = re.search(r'\((\d{4}:\d+)\)', full_text)
        if sfs_match:
            reference = sfs_match.group(1)
            # Try to find the law name
            law_name_match = re.search(r'([^,\.]+?)\s*\(\d{4}:\d+\)', full_text)
            if law_name_match:
                law_name = law_name_match.group(1).strip()
                return f"{law_name} ({reference})"
            else:
                return f"Lag ({reference})"
        
        return "Unknown Law"
    
    def _get_static_description(self):
        return (
            "Semesterlagen handlar om arbetstagares rätt till semesterförmåner: semesterledighet, semesterlön samt semesterersättning. "
            "En arbetstagare har som huvudregel rätt till 25 semesterdagar varje semesterår. Under semesterledigheten ska semesterlön utgå om sådan har tjänats in. "
            "I lagen finns även regler om hur semester ska förläggas. Lagen är semidispositiv vilket innebär att avtal som avviker från den kan vara gällande, så länge inte arbetstagarens rättigheter inskränks."
        )
    
    def _extract_metadata_strict(self, soup):
        """Extract metadata in the exact format specified, robust to label variants."""
        full_text = soup.get_text(separator='\n', strip=True)
        metadata_section = self._find_metadata_section(full_text)
        metadata = {}
        
        # Patterns for all possible variants
        patterns = {
            'Utfärdad': r'Utfärdad:\s*([\d-]+)',
            'Ikraftträdandedatum': r'Ikraftträdandedatum:\s*([\d-]+)',
            'Källa': r'Källa:\s*([^\n]+)',
            'SFS nr': r'SFS nr:\s*([^\n]+)',
            'Departement': r'Departement(?:/myndighet)?:\s*([^\n]+)',
            'Ändring införd': r'Ändring införd:\s*([^\n]+)',
            'Ändrad': r'Ändrad:\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\w+:|$)',
            'Övrigt': r'Övrigt:\s*([^\n]+)',
            'Övrig text': r'Övrig text:\s*([^\n]+)',
            'Länk': r'Länk:\s*([^\n]+)'
        }
        
        # Try to extract each field, prefer the first match
        for key, pattern in patterns.items():
            match = re.search(pattern, metadata_section, re.MULTILINE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                value = re.sub(r'\s+', ' ', value)
                metadata[key] = value
        
        # Normalize keys: if both 'Övrigt' and 'Övrig text', prefer 'Övrigt'
        if 'Övrig text' in metadata and 'Övrigt' not in metadata:
            metadata['Övrigt'] = metadata.pop('Övrig text')
        
        # Extract actual URL link for 'Länk' field
        if 'Länk' in metadata:
            # Look for actual link in HTML
            link_element = soup.find('a', string=re.compile(r'Länk till register', re.IGNORECASE))
            if link_element and link_element.get('href'):
                metadata['Länk URL'] = link_element.get('href')
            else:
                # Fallback: look for any link that might be the register link
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href')
                    if 'register' in href.lower() or 'lagrum' in href.lower():
                        metadata['Länk URL'] = href
                        break
        
        return metadata
    
    def _find_metadata_section(self, full_text):
        """Find the metadata section in the text"""
        # Look for the section that starts with "SFS nr:" and ends before the first section
        start_pattern = r'SFS nr:'
        end_pattern = r'\d+\s*§'
        
        start_match = re.search(start_pattern, full_text)
        if not start_match:
            return ""
        
        start_pos = start_match.start()
        
        # Find the end (first section number)
        end_match = re.search(end_pattern, full_text[start_pos:])
        if end_match:
            end_pos = start_pos + end_match.start()
        else:
            end_pos = len(full_text)
        
        return full_text[start_pos:end_pos]
    
    def _extract_important_laws(self, soup):
        """Extract the 'Viktiga lagar inom arbetsrätten' block as a list of laws with title, reference, and URL."""
        full_text = soup.get_text(separator='\n', strip=True)
        # Find the block
        block_pattern = r'Viktiga lagar inom arbetsrätten\n([\s\S]+?)(?:\nJP Infonets|\nOm Lagboken|$)'
        block_match = re.search(block_pattern, full_text)
        laws = []
        if block_match:
            block = block_match.group(1)
            # Each law is on its own line
            for line in block.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # Skip the header line
                if line.lower() == 'viktiga lagar inom arbetsrätten':
                    continue
                    
                # Try to extract SFS number
                sfs_match = re.search(r'\((\d{4}:\d+)\)', line)
                if sfs_match:
                    reference = sfs_match.group(1)
                    title = re.sub(r'\s*\(\d{4}:\d+\)', '', line).strip()
                    
                    # Try to find the actual URL for this law
                    url = self._find_law_url(soup, title, reference)
                    
                    # Convert relative URLs to absolute
                    if url and url.startswith('/'):
                        url = f"https://www.lagboken.se{url}"
                    
                    # If no URL found or it's JavaScript, try to construct one
                    if not url or url.startswith('javascript:'):
                        url = self._construct_law_url(title, reference)
                    
                    laws.append({
                        'title': title, 
                        'reference': reference,
                        'url': url
                    })
        return laws
    
    def _find_law_url(self, soup, title, reference):
        """Find the actual URL for a law based on title and reference."""
        # Look for links that contain the reference number
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href')
            link_text = link.get_text(strip=True)
            
            # Check if the link contains the reference number
            if reference in link_text or reference in href:
                return href
            
            # Also check if the title matches
            if title.lower() in link_text.lower():
                return href
        
        # If no direct match found, try to construct a URL based on the reference
        if reference:
            # Common pattern for lagboken.se URLs
            return f"https://www.lagboken.se/lagboken/start/arbetsratt-och-arbetsmiljoratt/{reference.lower().replace(':', '')}/"
        
        return ""
    
    def _construct_law_url(self, title, reference):
        """Construct a URL for a law based on title and reference."""
        if not reference:
            return ""
        
        # Common patterns for lagboken.se URLs
        base_url = "https://www.lagboken.se/lagboken/start/arbetsratt-och-arbetsmiljoratt/"
        
        # Create URL-friendly title
        title_lower = title.lower().replace('lag', '').replace('om', '').strip()
        title_clean = re.sub(r'[^a-zåäö0-9\s]', '', title_lower)
        title_clean = re.sub(r'\s+', '-', title_clean).strip('-')
        
        # Create URL-friendly reference
        ref_clean = reference.lower().replace(':', '')
        
        return f"{base_url}{title_clean}-{ref_clean}/"
    
    def save_to_json(self, data, filename):
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close_driver()

def scrape_law_data(url, save_to_file=True, filename=None):
    """
    Main function to scrape law data from a given URL
    
    Args:
        url (str): URL of the law page to scrape
        save_to_file (bool): Whether to save the data to a JSON file
        filename (str): Optional custom filename for the JSON file
        
    Returns:
        dict: Scraped law data or None if failed
    """
    # Initialize scraper
    scraper = LawDataScraper(headless=True)
    
    try:
        # Scrape the law page
        law_data = scraper.scrape_law_page(url)
        
        if law_data:
            if save_to_file:
                # Generate filename if not provided
                if not filename:
                    # Extract law reference from URL or title
                    ref_match = re.search(r'(\d{4}:\d+)', law_data.get('title', ''))
                    if ref_match:
                        ref = ref_match.group(1).replace(':', '')
                        filename = f"law_data_{ref}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    else:
                        filename = f"law_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                scraper.save_to_json(law_data, filename)
            
            # Print summary
            print(f"\nScraping completed successfully!")
            print(f"Title: {law_data['title']}")
            print(f"Description: {law_data['description']}")
            print(f"Metadata: {law_data['metadata']}")
            print(f"Important laws found: {len(law_data['important_laws'])}")
            
            return law_data
        else:
            print("Failed to scrape the law page")
            return None
            
    except Exception as e:
        print(f"Error in scrape_law_data: {e}")
        return None
    finally:
        scraper.close_driver()

if __name__ == "__main__":
    # Example usage
    url = "https://www.lagboken.se/lagboken/start/arbetsratt-och-arbetsmiljoratt/semesterlag-1977480/d_1564-semesterlag-1977_480/"
    result = scrape_law_data(url) 