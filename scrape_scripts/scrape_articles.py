import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import json
from pathlib import Path

from bs4 import BeautifulSoup

from scrape_scripts.utils import fetch_html, make_soup, get_text


def choose_best_container(soup: BeautifulSoup):
    candidates = [
        ("article", soup.find("article")),
        ("main", soup.find("main")),
        ("body", soup.find("body")),
    ]

    best_name = None
    best_el = None
    best_count = -1

    for name, el in candidates:
        if el is None:
            continue
        count = len(el.find_all("p"))
        if count > best_count:
            best_name = name
            best_el = el
            best_count = count

    return best_name, best_el


def parse_article(url: str) -> dict | None:
    html = fetch_html(url)
    if html is None:
        return None

    soup = make_soup(html)

    title = get_text(soup.find("h1"))
    if not title:
        print(f"[WARN] No title found: {url}")
        return None

    container_name, container = choose_best_container(soup)
    if container is None:
        print(f"[WARN] No content container found: {url}")
        return None

    raw_paragraphs = [get_text(p) for p in container.find_all("p")]
    raw_paragraphs = [p for p in raw_paragraphs if p]

    if not raw_paragraphs:
        print(f"[WARN] No paragraph text found: {url}")
        return None

    author = None
    role = None
    updated = None

    body_start = 0
    if len(raw_paragraphs) >= 4 and raw_paragraphs[0] == "Patienthåndbogen":
        author = raw_paragraphs[1]
        role = raw_paragraphs[2]
        if raw_paragraphs[3].startswith("Opdateret:"):
            updated = raw_paragraphs[3].replace("Opdateret:", "").strip()
            body_start = 4

    stop_phrases = [
        "Fagmedarbejdere",
        "Indhold leveret af",
        "Disclaimer",
        "Kristianiagade",
    ]
    skip_starts = [
        "Se animation",
    ]
    skip_exact = {
        "Patienthåndbogen",
    }

    cleaned_body: list[str] = []
    for text in raw_paragraphs[body_start:]:
        if text in skip_exact:
            continue
        if any(text.startswith(prefix) for prefix in stop_phrases):
            break
        if any(text.startswith(prefix) for prefix in skip_starts):
            continue
        cleaned_body.append(text)

    content = "\n".join(cleaned_body).strip()
    if len(content) < 150:
        print(f"[WARN] Very short content, skipping: {url}")
        return None

    return {
        "url": url,
        "title": title,
        "author": author,
        "role": role,
        "updated": updated,
        "source": "sundhed.dk",
        "domain": "virusinfektioner",
        "container": container_name,
        "content": content,
    }


def main() -> None:
    links_path = Path("data/raw/virusinfektioner_links.json")
    output_path = Path("data/processed/virusinfektioner_articles.jsonl")

    if not links_path.exists():
        raise FileNotFoundError(
            "Run collect_links.py first so data/raw/virusinfektioner_links.json exists."
        )

    with links_path.open("r", encoding="utf-8") as f:
        urls: list[str] = json.load(f)

    saved = 0
    with output_path.open("w", encoding="utf-8") as out:
        for url in urls:
            article = parse_article(url)
            if article is None:
                continue

            out.write(json.dumps(article, ensure_ascii=False) + "\n")
            saved += 1
            print(f"[OK] Saved: {article['title']}")

    print(f"\nSaved {saved} articles to {output_path}")


if __name__ == "__main__":
    main()