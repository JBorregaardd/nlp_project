import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))





import json
from collections import deque
from scrape_config import START_URL, ALLOWED_PREFIX, BRANCH_PREFIX
from scrape_scripts.utils import fetch_html, make_soup, extract_internal_links


def is_relevant_link(url: str) -> bool:
    if not url.startswith(ALLOWED_PREFIX):
        return False
    if not url.startswith(BRANCH_PREFIX):
        return False

    blocked_parts = [
        "/om-patienthaandbogen/",
        "?",
        "#",
    ]
    return not any(part in url for part in blocked_parts)


def main() -> None:
    visited: set[str] = set()
    discovered: set[str] = set()
    queue = deque([START_URL.rstrip("/") + "/"])

    while queue:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        html = fetch_html(url)
        if html is None:
            continue

        soup = make_soup(html)
        links = extract_internal_links(soup, url)

        branch_links = {link for link in links if is_relevant_link(link)}
        discovered.update(branch_links)

        for link in sorted(branch_links):
            if link not in visited:
                queue.append(link)

    output = sorted(discovered)
    print(f"\nCollected {len(output)} links")

    with open("data/raw/virusinfektioner_links.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("Saved links to data/raw/virusinfektioner_links.json")


if __name__ == "__main__":
    main()