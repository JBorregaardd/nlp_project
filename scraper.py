import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "da-DK,da;q=0.9,en;q=0.8",
}


def get_text(el):
    return el.get_text(" ", strip=True) if el else ""


def clean_paragraphs(paragraphs):
    cleaned = []
    stop_phrases = [
        "Fagmedarbejdere",
        "Indhold leveret af",
        "Disclaimer:",
        "Kristianiagade",
    ]

    skip_exact = {
        "Patienthåndbogen",
    }

    for p in paragraphs:
        text = get_text(p)
        if not text:
            continue

        if text in skip_exact:
            print(f"Skipping metadata line: {text}")
            continue

        if any(text.startswith(phrase) for phrase in stop_phrases):
            print(f"Stopping at footer/meta: {text[:100]}")
            break

        cleaned.append(text)

    return cleaned


def choose_best_container(soup):
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
            print(f"Container {name}: not found")
            continue

        paragraphs = el.find_all("p")
        print(f"Container {name}: {len(paragraphs)} <p> tags")

        if len(paragraphs) > best_count:
            best_name = name
            best_el = el
            best_count = len(paragraphs)

    return best_name, best_el


def extract_article(url, debug=False):
    print(f"\n--- Fetching: {url} ---")

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
    except Exception as e:
        print(f"Request error: {e}")
        return None

    print(f"Status code: {response.status_code}")

    if response.status_code != 200:
        print("Non-200 response")
        print(response.text[:300])
        return None

    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(response.text)

    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("h1")
    title = get_text(title_tag)
    print("Title:", title)

    container_name, content_div = choose_best_container(soup)
    if content_div is None:
        print("No usable container found")
        return None

    print(f"Using container: {container_name}")

    paragraphs = content_div.find_all("p")
    print(f"Found {len(paragraphs)} raw paragraphs in chosen container")

    if debug:
        for i, p in enumerate(paragraphs[:60]):
            print(f"[{i}] {get_text(p)[:200]}")

    cleaned_paragraphs = clean_paragraphs(paragraphs)
    print(f"Kept {len(cleaned_paragraphs)} cleaned paragraphs")

    content = "\n".join(cleaned_paragraphs).strip()
    if not content:
        print("Extracted content is empty")
        return None

    return {
        "url": url,
        "title": title,
        "content": content,
    }


if __name__ == "__main__":
    test_url = "https://www.sundhed.dk/borger/patienthaandbogen/hjerte-og-blodkar/sygdomme/hoejt-blodtryk-hypertension/hoejt-blodtryk/"
    result = extract_article(test_url, debug=True)

    print("\nResult preview:")
    if result:
        print("Title:", result["title"])
        print("Content preview:")
        print(result["content"][:1200])
    else:
        print(result)