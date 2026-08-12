"""
Server-side URL fetching + main-content extraction.

Kept intentionally simple: fetch the page, strip script/style/nav/footer
tags, pull visible text. No headless browser (no JS rendering) -- that's
a real limitation for JS-heavy SPAs, documented in the README.
"""
import requests
from bs4 import BeautifulSoup

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

_STRIP_TAGS = ("script", "style", "nav", "footer", "header", "noscript", "svg", "form")


class UrlFetchError(Exception):
    """Raised when a URL cannot be fetched or contains no usable content."""


def fetch_url_content(url: str) -> tuple[str, str | None]:
    """Fetch a URL and return (plain_text_content, page_title)."""
    try:
        response = requests.get(
            url,
            timeout=settings.fetch_timeout_seconds,
            headers={"User-Agent": "AI-Knowledge-Inbox/1.0 (+ingestion bot)"},
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise UrlFetchError(f"Timed out fetching {url}") from exc
    except requests.exceptions.RequestException as exc:
        raise UrlFetchError(f"Failed to fetch {url}: {exc}") from exc

    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type and "text/plain" not in content_type:
        raise UrlFetchError(f"Unsupported content-type '{content_type}' for {url}")

    soup = BeautifulSoup(response.text, "html.parser")

    for tag_name in _STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else None

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)

    if not text:
        raise UrlFetchError(f"No extractable text content at {url}")

    if len(text) > settings.max_page_chars:
        logger.info(
            "Truncating fetched page content",
            extra={"extra_fields": {"url": url, "original_len": len(text)}},
        )
        text = text[: settings.max_page_chars]

    return text, title
