

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class CrawledPage:
    url: str
    domain: str
    path: str
    title: Optional[str] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    status_code: Optional[int] = None
    crawled_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
