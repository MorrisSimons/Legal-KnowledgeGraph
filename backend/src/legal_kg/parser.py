from typing import List, Dict
from bs4 import BeautifulSoup
from .database import get_connection

def get_links_from_db(url: str) -> List[str]:
    """
    Fetch the HTML content for the given URL from the database,
    parse it, and extract all links (hrefs) from <a> tags.
    Returns a list of URLs found.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT html_content FROM crawled_pages WHERE url = ?",
        (url,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row or not row[0]:
        return []
    html = row[0]
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a_tag in soup.find_all("a", href=True):
        links.append(a_tag["href"])
    return links

