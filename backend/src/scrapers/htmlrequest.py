"""
HTML Request and Content Extractor Module
Extracts clean, readable text/markdown from target company websites.
"""
import logging
import asyncio
from typing import Optional, Dict
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

class ContentExtractor:
    """Fetches web pages and extracts compact, clean text suitable for LLM evaluation."""

    def __init__(self, timeout_seconds: float = 12.0):
        self.timeout = timeout_seconds

    async def fetch_page_text(self, url: str) -> Optional[Dict[str, str]]:
        """
        Fetches a target webpage and extracts text, title, and meta description.
        Returns None if fetch fails.
        """
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        try:
            async with httpx.AsyncClient(
                headers=DEFAULT_HEADERS, 
                follow_redirects=True, 
                timeout=self.timeout,
                verify=False
            ) as client:
                response = await client.get(url)
                if response.status_code >= 400:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status_code}")
                    return None

                return self._parse_html(response.text, url)
        except Exception as e:
            logger.warning(f"Error fetching page {url}: {e}")
            return None

    def _parse_html(self, html_content: str, url: str) -> Dict[str, str]:
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove irrelevant elements (scripts, styles, noscript, svg, navigation bars)
        for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "iframe"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        
        # Meta description
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag["content"].strip()

        # Extract main text
        text_content = soup.get_text(separator="\n", strip=True)
        # Limit text length to ~6000 characters to keep LLM context clean and token-efficient
        truncated_text = text_content[:6000]

        return {
            "url": url,
            "title": title,
            "description": meta_desc,
            "body_text": truncated_text
        }
