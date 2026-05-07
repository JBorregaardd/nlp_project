def load_stopwords(path="data/stopord.txt"):
    with open(path, "r", encoding="utf-8") as f:
        return {
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        }


STOPWORDS = load_stopwords()


def clean_query_for_retrieval(query: str) -> str:
    tokens = query.lower().split()
    filtered = [t for t in tokens if t not in STOPWORDS]

    if not filtered:
        return query

    return " ".join(filtered)