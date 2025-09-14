import requests
from urllib.parse import urlparse
from datetime import datetime
from .models import CrawledPage
from .database import get_connection


def crawl_url(url: str) -> CrawledPage:
    """
    Simple function to crawl a single URL and return a CrawledPage object.
    KISS principle - just fetch HTML and return basic info.
    """
    try:
        # Parse URL to extract domain and path
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path or "/"
        
        # Fetch the page
        response = requests.get(url, timeout=30)
        
        # Create CrawledPage object
        crawled_page = CrawledPage(
            url=url,
            domain=domain,
            path=path,
            html_content=response.text,
            status_code=response.status_code,
            crawled_at=datetime.now()
        )
        
        return crawled_page
        
    except Exception as e:
        # Return a page object with error info
        parsed_url = urlparse(url)
        return CrawledPage(
            url=url,
            domain=parsed_url.netloc,
            path=parsed_url.path or "/",
            status_code=0,
            crawled_at=datetime.now(),
            metadata={"error": str(e)}
        )


def save_crawled_page(crawled_page: CrawledPage) -> bool:
    """
    Save a CrawledPage object to the database.
    Returns True if successful, False otherwise.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO crawled_pages 
            (url, domain, path, title, html_content, text_content, status_code, crawled_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            crawled_page.url,
            crawled_page.domain,
            crawled_page.path,
            crawled_page.title,
            crawled_page.html_content,
            crawled_page.text_content,
            crawled_page.status_code,
            crawled_page.crawled_at,
            str(crawled_page.metadata) if crawled_page.metadata else None
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error saving to database: {e}")
        return False


def crawl_and_save(url: str) -> bool:
    """
    Simple function to crawl a URL and save it to the database.
    One-stop function following KISS principle.
    """
    print(f"Crawling: {url}")
    crawled_page = crawl_url(url)
    
    if crawled_page.status_code == 200:
        print(f"Successfully crawled {url}")
    else:
        print(f"Failed to crawl {url} - Status: {crawled_page.status_code}")
    
    success = save_crawled_page(crawled_page)
    
    if success:
        print(f"Successfully saved {url} to database")
    else:
        print(f"Failed to save {url} to database")
    
    return success


if __name__ == "__main__":
    # Test with the seed URL
    seed_url = "https://www.lagboken.se/lagboken/start/"
    crawl_and_save(seed_url)
