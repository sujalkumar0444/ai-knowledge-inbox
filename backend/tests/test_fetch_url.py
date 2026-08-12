import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.fetch_url import UrlFetchError, fetch_url_content


def _mock_response(text, status_code=200, content_type="text/html"):
    resp = Mock()
    resp.status_code = status_code
    resp.headers = {"content-type": content_type}
    resp.text = text
    resp.raise_for_status = Mock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"{status_code} error"
        )
    return resp


def test_fetch_extracts_visible_text_and_title():
    html = """
    <html><head><title>Test Page</title></head>
    <body>
        <nav>Nav link</nav>
        <script>console.log('should be stripped')</script>
        <p>Real paragraph content here.</p>
        <footer>Footer junk</footer>
    </body></html>
    """
    with patch("app.services.fetch_url.requests.get", return_value=_mock_response(html)):
        text, title = fetch_url_content("https://example.com")

    assert title == "Test Page"
    assert "Real paragraph content here." in text
    assert "should be stripped" not in text
    assert "Nav link" not in text
    assert "Footer junk" not in text


def test_fetch_raises_on_timeout():
    with patch(
        "app.services.fetch_url.requests.get",
        side_effect=requests.exceptions.Timeout(),
    ):
        with pytest.raises(UrlFetchError, match="Timed out"):
            fetch_url_content("https://slow.example.com")


def test_fetch_raises_on_http_error():
    resp = _mock_response("<html></html>", status_code=404)
    with patch("app.services.fetch_url.requests.get", return_value=resp):
        with pytest.raises(UrlFetchError):
            fetch_url_content("https://example.com/missing")


def test_fetch_rejects_non_html_content_type():
    resp = _mock_response("binary junk", content_type="application/octet-stream")
    with patch("app.services.fetch_url.requests.get", return_value=resp):
        with pytest.raises(UrlFetchError, match="Unsupported content-type"):
            fetch_url_content("https://example.com/file.bin")


def test_fetch_raises_on_empty_extractable_text():
    html = "<html><body><script>only script content</script></body></html>"
    with patch("app.services.fetch_url.requests.get", return_value=_mock_response(html)):
        with pytest.raises(UrlFetchError, match="No extractable text"):
            fetch_url_content("https://example.com/empty")


def test_fetch_truncates_very_long_pages():
    html = f"<html><body><p>{'word ' * 20000}</p></body></html>"
    with patch("app.services.fetch_url.requests.get", return_value=_mock_response(html)):
        text, _ = fetch_url_content("https://example.com/long")

    from app.config import settings

    assert len(text) <= settings.max_page_chars
