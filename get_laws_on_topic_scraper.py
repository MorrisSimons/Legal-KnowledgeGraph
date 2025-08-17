import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
import json
import re
from datetime import datetime
import time
from typing import List, Dict, Optional

class GetLawsOnTopicScraper:
    def __init__(self):
        """
        Initialize the Get Laws On Topic Scraper
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_topic_page(self, url):
        """
        Scrape a topic page to get all law links (single page only)
        """
        try:
            print(f"Scraping topic page: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            law_links = self._extract_all_law_links(soup)
            topic_info = self._extract_topic_info(soup, url)
            topic_page_data = {
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'topic_info': topic_info,
                'total_laws_found': len(law_links),
                'laws': law_links
            }
            return topic_page_data
        except Exception as e:
            print(f"Error scraping topic page: {e}")
            return None

    def scrape_topic_all_pages(self, url):
        """
        Scrape all paginated pages for a topic and collect all law links.
        """
        all_laws = []
        page_num = 1
        next_url = url
        topic_info = None
        visited_urls = set()
        
        while next_url and next_url not in visited_urls:
            visited_urls.add(next_url)
            print(f"Scraping topic page {page_num}: {next_url}")
            
            try:
                response = self.session.get(next_url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                if topic_info is None:
                    topic_info = self._extract_topic_info(soup, url)
                
                page_laws = self._extract_all_law_links(soup)
                print(f"  Found {len(page_laws)} laws on this page.")
                all_laws.extend(page_laws)
                
                # DEBUG: Print all <a> tags and their text to inspect pagination
                print("  Pagination links on this page:")
                for a in soup.find_all('a', href=True):
                    print(f"    text: '{a.get_text(strip=True)}' | href: {a['href']}")
                
                # Find next page link with multiple strategies
                next_url = self._find_next_page_link(soup, next_url)
                
                page_num += 1
                
            except Exception as e:
                print(f"Error scraping page {next_url}: {e}")
                break
        
        print(f"Total laws collected from all pages: {len(all_laws)}")
        
        topic_page_data = {
            'url': url,
            'scraped_at': datetime.now().isoformat(),
            'topic_info': topic_info or {},
            'total_laws_found': len(all_laws),
            'laws': all_laws
        }
        return topic_page_data
    
    def _find_next_page_link(self, soup, current_url):
        """
        Find the next page link using multiple strategies, including the → arrow.
        """
        # Strategy 1: Look for right arrow (→) link
        arrow_link = soup.find('a', string=lambda s: s and s.strip() == '→')
        if isinstance(arrow_link, Tag):
            href = arrow_link.get('href')
            if isinstance(href, str) and href:
                return self._construct_full_url(href, current_url)
        
        # Strategy 2: Look for next page number
        pagination_links = soup.find_all('a', href=True)
        current_page_num = self._extract_page_number(current_url)
        for link in pagination_links:
            href = link.get('href', '')
            if not isinstance(href, str):
                continue
            link_text = link.get_text(strip=True)
            if re.match(r'^\d+$', link_text):
                page_num = int(link_text)
                if page_num == current_page_num + 1:
                    return self._construct_full_url(href, current_url)
        
        # Fallback: previous strategies
        # Look for "nästa" link
        next_link = soup.find('a', string=re.compile(r'nästa', re.IGNORECASE))
        if isinstance(next_link, Tag):
            href = next_link.get('href')
            if isinstance(href, str) and href:
                return self._construct_full_url(href, current_url)
        # Look for "next" link
        next_link = soup.find('a', string=re.compile(r'next', re.IGNORECASE))
        if isinstance(next_link, Tag):
            href = next_link.get('href')
            if isinstance(href, str) and href:
                return self._construct_full_url(href, current_url)
        # Look for links containing "page" or "sida"
        for link in pagination_links:
            href = link.get('href', '')
            if not isinstance(href, str):
                continue
            if 'page' in href.lower() or 'sida' in href.lower():
                if self._is_next_page_link(href, current_url):
                    return self._construct_full_url(href, current_url)
        return None
    
    def _construct_full_url(self, href, current_url):
        """Construct full URL from relative href and current URL"""
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return f"https://www.lagboken.se{href}"
        elif href.startswith('?'):
            # Handle query parameters - combine with base URL
            base_url = current_url.split('?')[0]  # Remove existing query params
            return f"{base_url}{href}"
        else:
            # Assume it's a relative path
            return f"https://www.lagboken.se/{href}"
    
    def _extract_page_number(self, url):
        """Extract page number from URL"""
        # Look for page parameter in URL
        page_match = re.search(r'[?&]page=(\d+)', url)
        if page_match:
            return int(page_match.group(1))
        
        # Look for page number in path
        page_match = re.search(r'/page/(\d+)', url)
        if page_match:
            return int(page_match.group(1))
        
        # Default to page 1 if no page number found
        return 1
    
    def _is_next_page_link(self, href, current_url):
        """Check if a link is likely a next page link"""
        current_page = self._extract_page_number(current_url)
        
        # Check if href contains next page number
        page_match = re.search(r'[?&]page=(\d+)', href)
        if page_match:
            return int(page_match.group(1)) == current_page + 1
        
        page_match = re.search(r'/page/(\d+)', href)
        if page_match:
            return int(page_match.group(1)) == current_page + 1
        
        return False

    def scrape_multiple_topic_pages(self, topic_urls, scrape_individual_laws=True, max_laws_per_topic=None, max_total_laws=None):
        """
        Scrape multiple topic pages and combine all law data into one comprehensive list
        
        Args:
            topic_urls (list): List of topic page URLs to scrape
            scrape_individual_laws (bool): Whether to scrape individual law details
            max_laws_per_topic (int): Maximum number of laws to scrape per topic (None for all)
            max_total_laws (int): Maximum total number of laws to scrape across all topics (None for all)
            
        Returns:
            dict: Complete data with all topic pages and combined law data
        """
        try:
            all_topic_data = []
            all_laws = []
            total_laws_scraped = 0
            
            print(f"Starting to scrape {len(topic_urls)} topic pages...")
            
            for i, topic_url in enumerate(topic_urls, 1):
                print(f"\n--- Topic {i}/{len(topic_urls)} ---")
                
                # Scrape all paginated pages for this topic
                topic_page_data = self.scrape_topic_all_pages(topic_url)
                if not topic_page_data:
                    print(f"Failed to scrape topic page {i}: {topic_url}")
                    continue
                
                all_topic_data.append(topic_page_data)
                print(f"Found {len(topic_page_data['laws'])} laws on topic: {topic_page_data['topic_info'].get('title', 'Unknown')}")
                
                # Limit laws per topic if specified
                laws_to_process = topic_page_data['laws']
                if max_laws_per_topic:
                    laws_to_process = laws_to_process[:max_laws_per_topic]
                    print(f"Processing first {len(laws_to_process)} laws from this topic")
                
                # Check if we've reached the total limit
                if max_total_laws and total_laws_scraped >= max_total_laws:
                    print(f"Reached total limit of {max_total_laws} laws, stopping...")
                    break
                
                # Calculate how many laws we can still scrape
                remaining_laws = max_total_laws - total_laws_scraped if max_total_laws else len(laws_to_process)
                if max_total_laws:
                    laws_to_process = laws_to_process[:remaining_laws]
                
                if scrape_individual_laws and laws_to_process:
                    # Import the law data scraper
                    try:
                        from law_datascraper import scrape_law_data
                    except ImportError:
                        print("Warning: law_datascraper not found. Individual law details will not be scraped.")
                        # Add topic page info to laws without individual details
                        for law in laws_to_process:
                            law['topic_page_info'] = topic_page_data['topic_info']
                            all_laws.append(law)
                        total_laws_scraped += len(laws_to_process)
                        continue
                    
                    # Scrape each individual law
                    for j, law in enumerate(laws_to_process, 1):
                        print(f"  Scraping law {j}/{len(laws_to_process)}: {law.get('title', 'Unknown')} ({law.get('reference', 'Unknown')})")
                        
                        try:
                            law_data = scrape_law_data(law['url'], save_to_file=False)
                            if law_data:
                                # Add the law info from topic page
                                law_data['topic_page_info'] = topic_page_data['topic_info']
                                law_data['topic_page_url'] = topic_url
                                all_laws.append(law_data)
                                total_laws_scraped += 1
                            else:
                                print(f"    Failed to scrape {law.get('title', 'Unknown')}")
                                # Add basic law info even if scraping failed
                                law['topic_page_info'] = topic_page_data['topic_info']
                                law['topic_page_url'] = topic_url
                                all_laws.append(law)
                                total_laws_scraped += 1
                        except Exception as e:
                            print(f"    Error scraping {law.get('title', 'Unknown')}: {e}")
                            # Add basic law info even if scraping failed
                            law['topic_page_info'] = topic_page_data['topic_info']
                            law['topic_page_url'] = topic_url
                            all_laws.append(law)
                            total_laws_scraped += 1
                        
                        # Add a small delay to be respectful to the server
                        time.sleep(1)
                        
                        # Check if we've reached the total limit
                        if max_total_laws and total_laws_scraped >= max_total_laws:
                            print(f"Reached total limit of {max_total_laws} laws, stopping...")
                            break
                else:
                    # Just add the law links without individual details
                    for law in laws_to_process:
                        law['topic_page_info'] = topic_page_data['topic_info']
                        law['topic_page_url'] = topic_url
                        all_laws.append(law)
                        total_laws_scraped += len(laws_to_process)
                
                if max_total_laws and total_laws_scraped >= max_total_laws:
                    break
            
            # Create complete dataset
            complete_data = {
                'topic_pages': all_topic_data,
                'all_laws': all_laws,
                'total_topics_scraped': len(all_topic_data),
                'total_laws_scraped': total_laws_scraped,
                'scraped_at': datetime.now().isoformat()
            }
            
            return complete_data
            
        except Exception as e:
            print(f"Error in scrape_multiple_topic_pages: {e}")
            return None
    
    def scrape_all_laws_from_topic(self, url, max_laws=None):
        """
        Scrape a topic page and then scrape all individual law pages
        
        Args:
            url (str): URL of the topic page
            max_laws (int): Maximum number of laws to scrape (None for all)
            
        Returns:
            dict: Complete data with topic page and all individual laws
        """
        try:
            # First scrape the topic page
            topic_page_data = self.scrape_topic_page(url)
            if not topic_page_data:
                return None
            
            print(f"Found {len(topic_page_data['laws'])} laws on topic page")
            
            # Limit the number of laws to scrape if specified
            laws_to_scrape = topic_page_data['laws']
            if max_laws:
                laws_to_scrape = laws_to_scrape[:max_laws]
                print(f"Will scrape first {len(laws_to_scrape)} laws")
            
            # Import the law data scraper
            try:
                from law_datascraper import scrape_law_data
            except ImportError:
                print("Warning: law_datascraper not found. Individual law details will not be scraped.")
                return topic_page_data
            
            # Scrape each individual law
            detailed_laws = []
            for i, law in enumerate(laws_to_scrape, 1):
                print(f"Scraping law {i}/{len(laws_to_scrape)}: {law['title']} ({law['reference']})")
                
                try:
                    law_data = scrape_law_data(law['url'], save_to_file=False)
                    if law_data:
                        # Add the law info from topic page
                        law_data['topic_page_info'] = law
                        detailed_laws.append(law_data)
                    else:
                        print(f"Failed to scrape {law['title']}")
                except Exception as e:
                    print(f"Error scraping {law['title']}: {e}")
                
                # Add a small delay to be respectful to the server
                time.sleep(1)
            
            # Create complete dataset
            complete_data = {
                'topic_page': topic_page_data,
                'detailed_laws': detailed_laws,
                'total_laws_scraped': len(detailed_laws),
                'scraped_at': datetime.now().isoformat()
            }
            
            return complete_data
            
        except Exception as e:
            print(f"Error in scrape_all_laws_from_topic: {e}")
            return None
    
    def _extract_topic_info(self, soup, url):
        """Extract topic information from the page"""
        topic_info = {}
        
        # Try to extract title
        title_selectors = [
            'h1',
            '.page-title',
            '.topic-title',
            '[class*="title"]',
            'h2'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) > 5:
                    topic_info['title'] = text
                    break
        
        # If no title found, try to extract from URL
        if 'title' not in topic_info:
            # Extract from URL path
            url_parts = url.split('/')
            if len(url_parts) > 2:
                # Get the last meaningful part of the URL
                for part in reversed(url_parts):
                    if part and part != 'start' and not part.startswith('http'):
                        topic_info['title'] = part.replace('-', ' ').title()
                        break
        
        # Extract description if available
        description_selectors = [
            'meta[name="description"]',
            '.description',
            '.topic-description',
            'p'
        ]
        
        for selector in description_selectors:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element and element.get('content'):
                    topic_info['description'] = element.get('content')
                    break
            else:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text and len(text) > 50 and len(text) < 500:
                        topic_info['description'] = text
                        break
        
        return topic_info
    
    def _extract_all_law_links(self, soup):
        """Extract all law links from the topic page"""
        law_links = []
        
        # Look for law links in the main content area
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            link_text = link.get_text(strip=True)
            
            # Check if this looks like a law link
            if self._is_law_link(href, link_text):
                # Extract law information
                law_info = self._extract_law_info_from_link(link_text, href)
                if law_info:
                    law_links.append(law_info)
        
        # Remove duplicates based on reference
        unique_laws = []
        seen_refs = set()
        for law in law_links:
            if law['reference'] not in seen_refs:
                unique_laws.append(law)
                seen_refs.add(law['reference'])
        
        return unique_laws
    
    def _is_law_link(self, href, link_text):
        """Check if a link looks like a law link"""
        # Check if href contains law-related patterns
        if any(pattern in href.lower() for pattern in ['lag', 'sfs', '197', '198', '199', '200', '201', '202']):
            return True
        
        # Check if link text contains law patterns
        if any(pattern in link_text.lower() for pattern in ['lag', 'sfs', '197', '198', '199', '200', '201', '202']):
            return True
        
        return False
    
    def _extract_law_info_from_link(self, link_text, href):
        """Extract law information from a link"""
        # Try to extract SFS number from link text
        sfs_match = re.search(r'\((\d{4}:\d+)\)', link_text)
        if sfs_match:
            reference = sfs_match.group(1)
            title = re.sub(r'\s*\(\d{4}:\d+\)', '', link_text).strip()
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                url = f"https://www.lagboken.se{href}"
            else:
                url = href
            
            return {
                'title': title,
                'reference': reference,
                'url': url
            }
        
        # If no SFS number found, try to extract from href
        href_match = re.search(r'(\d{4}):(\d+)', href)
        if href_match:
            year = href_match.group(1)
            number = href_match.group(2)
            reference = f"{year}:{number}"
            
            # Clean up title
            title = link_text.strip()
            if not title:
                title = f"Lag ({reference})"
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                url = f"https://www.lagboken.se{href}"
            else:
                url = href
            
            return {
                'title': title,
                'reference': reference,
                'url': url
            }
        
        return None
    
    def save_to_json(self, data, filename):
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")

def get_laws_on_topic(url, save_to_file=True, filename=None, scrape_all_pages=True, max_laws=None):
    """
    Main function to get all laws from a topic page and optionally scrape all individual law pages
    
    Args:
        url (str): URL of the topic page to scrape
        save_to_file (bool): Whether to save the data to a JSON file
        filename (str): Optional custom filename for the JSON file
        scrape_all_pages (bool): Whether to scrape all individual law pages (True) or just get links (False)
        max_laws (int): Maximum number of laws to scrape (None for all)
        
    Returns:
        dict: Scraped topic data with law links and optionally detailed laws, or None if failed
    """
    # Initialize scraper
    scraper = GetLawsOnTopicScraper()
    
    try:
        if scrape_all_pages:
            # Scrape topic page and all individual law pages
            topic_data = scraper.scrape_all_laws_from_topic(url, max_laws)
        else:
            # Scrape only the topic page
            topic_data = scraper.scrape_topic_page(url)
        
        if topic_data:
            if save_to_file:
                # Generate filename if not provided
                if not filename:
                    if scrape_all_pages:
                        topic_title = topic_data.get('topic_page', {}).get('topic_info', {}).get('title', 'topic')
                    else:
                        topic_title = topic_data.get('topic_info', {}).get('title', 'topic')
                    
                    # Clean up title for filename
                    clean_title = re.sub(r'[^a-zA-Z0-9åäöÅÄÖ\s]', '', topic_title)
                    clean_title = re.sub(r'\s+', '_', clean_title).strip('_')
                    
                    if scrape_all_pages:
                        filename = f"topic_all_laws_{clean_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    else:
                        filename = f"topic_laws_{clean_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                scraper.save_to_json(topic_data, filename)
            
            # Print summary
            print(f"\nTopic scraping completed successfully!")
            
            if scrape_all_pages:
                topic_info = topic_data.get('topic_page', {}).get('topic_info', {})
                total_laws = topic_data.get('topic_page', {}).get('total_laws_found', 0)
                scraped_laws = topic_data.get('total_laws_scraped', 0)
                print(f"Topic: {topic_info.get('title', 'Unknown')}")
                print(f"Total laws found: {total_laws}")
                print(f"Laws scraped: {scraped_laws}")
            else:
                topic_info = topic_data.get('topic_info', {})
                total_laws = topic_data.get('total_laws_found', 0)
                print(f"Topic: {topic_info.get('title', 'Unknown')}")
                print(f"Total laws found: {total_laws}")
            
            # Show first few laws as preview
            if scrape_all_pages:
                laws = topic_data.get('topic_page', {}).get('laws', [])
            else:
                laws = topic_data.get('laws', [])
                
            if laws:
                print(f"\nFirst 5 laws found:")
                for i, law in enumerate(laws[:5], 1):
                    print(f"{i}. {law['title']} ({law['reference']})")
            
            return topic_data
        else:
            print("Failed to scrape the topic page")
            return None
            
    except Exception as e:
        print(f"Error in get_laws_on_topic: {e}")
        return None

def get_laws_from_multiple_topics(topic_urls, save_to_file=True, filename=None, scrape_individual_laws=True, max_laws_per_topic=None, max_total_laws=None):
    """
    Main function to get all laws from multiple topic pages and combine into one comprehensive list
    
    Args:
        topic_urls (list): List of topic page URLs to scrape
        save_to_file (bool): Whether to save the data to a JSON file
        filename (str): Optional custom filename for the JSON file
        scrape_individual_laws (bool): Whether to scrape individual law details
        max_laws_per_topic (int): Maximum number of laws to scrape per topic (None for all)
        max_total_laws (int): Maximum total number of laws to scrape across all topics (None for all)
        
    Returns:
        dict: Complete data with all topic pages and combined law data, or None if failed
    """
    # Initialize scraper
    scraper = GetLawsOnTopicScraper()
    
    try:
        # Scrape multiple topic pages
        complete_data = scraper.scrape_multiple_topic_pages(
            topic_urls, 
            scrape_individual_laws, 
            max_laws_per_topic, 
            max_total_laws
        )
        
        if complete_data:
            if save_to_file:
                # Generate filename if not provided
                if not filename:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    if scrape_individual_laws:
                        filename = f"multiple_topics_comprehensive_{timestamp}.json"
                    else:
                        filename = f"multiple_topics_links_{timestamp}.json"
                
                scraper.save_to_json(complete_data, filename)
            
            # Print summary
            print(f"\nMultiple topic scraping completed successfully!")
            print(f"Topics scraped: {complete_data.get('total_topics_scraped', 0)}")
            print(f"Total laws scraped: {complete_data.get('total_laws_scraped', 0)}")
            
            # Show topic summary
            topic_pages = complete_data.get('topic_pages', [])
            if topic_pages:
                print(f"\nTopics processed:")
                for i, topic in enumerate(topic_pages, 1):
                    topic_info = topic.get('topic_info', {})
                    total_laws = topic.get('total_laws_found', 0)
                    print(f"  {i}. {topic_info.get('title', 'Unknown')} - {total_laws} laws")
            
            # Show first few laws as preview
            all_laws = complete_data.get('all_laws', [])
            if all_laws:
                print(f"\nFirst 5 laws from all topics:")
                for i, law in enumerate(all_laws[:5], 1):
                    topic_info = law.get('topic_page_info', {})
                    topic_title = topic_info.get('title', 'Unknown')
                    print(f"  {i}. {law['title']} ({law['reference']}) - from {topic_title}")
            
            return complete_data
        else:
            print("Failed to scrape the topic pages")
            return None
            
    except Exception as e:
        print(f"Error in get_laws_from_multiple_topics: {e}")
        return None

if __name__ == "__main__":
    # Example usage for multiple topic pages
    topic_urls = [
        "https://www.lagboken.se/lagboken/start/arbetsratt-och-arbetsmiljoratt/",
        # Add more topic URLs here as needed
    ]
    
    # Scrape multiple topic pages with comprehensive data
    result = get_laws_from_multiple_topics(
        topic_urls=topic_urls,
        scrape_individual_laws=True,
        max_laws_per_topic=2,  # Limit to first 2 laws per topic
        max_total_laws=5       # Limit to total 5 laws across all topics
    ) 