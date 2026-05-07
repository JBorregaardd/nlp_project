import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import time
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

from scrape_config import HEADERS, TIMEOUT_SECONDS, REQUEST_DELAY_SECONDS


def fetch_html(url: str) -> str | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        print(f"[ERROR] Request failed for {url}: {exc}")
        return None

    print(f"[INFO] {response.status_code} {url}")

    if response.status_code != 200:
        return None

    time.sleep(REQUEST_DELAY_SECONDS)
    return response.text


def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def normalize_url(base_url: str, href: str) -> str | None:
    if not href:
        return None
    absolute = urljoin(base_url, href)
    absolute, _ = urldefrag(absolute)

    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"}:
        return None

    return absolute.rstrip("/") + "/"


def extract_internal_links(soup: BeautifulSoup, base_url: str) -> set[str]:
    links: set[str] = set()

    for a in soup.find_all("a", href=True):
        normalized = normalize_url(base_url, a["href"])
        if normalized:
            links.add(normalized)

    return links


def get_text(element) -> str:
    if element is None:
        return ""
    return element.get_text(" ", strip=True)