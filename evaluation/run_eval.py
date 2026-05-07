import json
from pathlib import Path

import requests


API_URL = "http://127.0.0.1:8000/v1/ask"
QUESTIONS_PATH = Path("evaluation/questions.json")


UNKNOWN_PHRASES = [
    "jeg ved det ikke",
    "jeg kan ikke finde relevant information",
    "ikke i de tilgængelige kilder",
    "fremgår ikke",
]


def normalize(text: str) -> str:
    return text.lower().strip()


def source_hit(sources, item) -> bool | None:
    expected_titles = []

    if item.get("expected_source_title"):
        expected_titles.append(item["expected_source_title"])

    expected_titles.extend(item.get("acceptable_source_titles", []))

    if not expected_titles:
        return None

    source_titles = [normalize(s.get("title", "")) for s in sources]

    for expected in expected_titles:
        expected_norm = normalize(expected)
        for title in source_titles:
            if expected_norm in title or title in expected_norm:
                return True

    return False


def keyword_coverage(answer: str, expected_keywords: list[str]) -> float:
    if not expected_keywords:
        return 0.0

    answer_norm = normalize(answer)

    hits = 0
    for keyword in expected_keywords:
        if normalize(keyword) in answer_norm:
            hits += 1

    return hits / len(expected_keywords)


def answer_is_unknown(answer: str) -> bool:
    answer_norm = normalize(answer)
    return any(phrase in answer_norm for phrase in UNKNOWN_PHRASES)


def evaluate_item(item, mode="sparse", top_k=5):
    response = requests.post(
        API_URL,
        json={
            "question": item["question"],
            "top_k": top_k,
            "mode": mode,
        },
        timeout=180,
    )

    response.raise_for_status()
    data = response.json()

    answer = data.get("answer", "")
    sources = data.get("sources", [])

    expected_behavior = item.get("expected_behavior", "answer_from_context")

    retrieval_hit = source_hit(sources, item)

    coverage = keyword_coverage(
        answer=answer,
        expected_keywords=item.get("expected_keywords", []),
    )

    unknown_ok = None
    if expected_behavior == "unknown":
        unknown_ok = answer_is_unknown(answer)

    return {
        "id": item["id"],
        "category": item["category"],
        "question": item["question"],
        "expected_behavior": expected_behavior,
        "expected_source_title": item.get("expected_source_title"),
        "retrieval_hit": retrieval_hit,
        "keyword_coverage": coverage,
        "unknown_ok": unknown_ok,
        "answer": answer,
        "sources": sources,
        "retrieval_query": data.get("retrieval_query"),
        "rewritten_query": data.get("rewritten_query"),
    }


def run_eval(mode="hybrid", top_k=3, limit=None):
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))

    if limit is not None:
        questions = questions[:limit]

    results = []

    for i, item in enumerate(questions, start=1):
        print(f"[{i}/{len(questions)}] {item['id']} - {item['question']}")

        try:
            result = evaluate_item(item, mode=mode, top_k=top_k)
        except Exception as exc:
            result = {
                "id": item["id"],
                "category": item["category"],
                "question": item["question"],
                "error": str(exc),
            }

        results.append(result)

        print(f"  retrieval_hit: {result.get('retrieval_hit')}")
        print(f"  keyword_coverage: {result.get('keyword_coverage')}")
        print(f"  unknown_ok: {result.get('unknown_ok')}")
        print()

    in_scope = [
        r for r in results
        if r.get("expected_behavior") != "unknown" and "error" not in r
    ]
    out_scope = [
        r for r in results
        if r.get("expected_behavior") == "unknown" and "error" not in r
    ]

    retrieval_values = [
        r["retrieval_hit"]
        for r in in_scope
        if r.get("retrieval_hit") is not None
    ]

    keyword_values = [
        r["keyword_coverage"]
        for r in in_scope
        if r.get("keyword_coverage") is not None
    ]

    unknown_values = [
        r["unknown_ok"]
        for r in out_scope
        if r.get("unknown_ok") is not None
    ]

    summary = {
        "mode": mode,
        "top_k": top_k,
        "num_questions": len(results),
        "num_in_scope": len(in_scope),
        "num_out_of_scope": len(out_scope),
        "retrieval_hit_rate": (
            sum(retrieval_values) / len(retrieval_values)
            if retrieval_values else None
        ),
        "avg_keyword_coverage": (
            sum(keyword_values) / len(keyword_values)
            if keyword_values else None
        ),
        "unknown_accuracy": (
            sum(unknown_values) / len(unknown_values)
            if unknown_values else None
        ),
        "results": results,
    }
    RESULTS_PATH = Path(f"evaluation/results_{mode}.json")
    RESULTS_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Summary")
    print("-------")
    print(f"Questions: {summary['num_questions']}")
    print(f"In-scope: {summary['num_in_scope']}")
    print(f"Out-of-scope: {summary['num_out_of_scope']}")
    print(f"Retrieval hit rate: {summary['retrieval_hit_rate']}")
    print(f"Average keyword coverage: {summary['avg_keyword_coverage']}")
    print(f"Unknown accuracy: {summary['unknown_accuracy']}")
    print(f"Saved to: {RESULTS_PATH}")


if __name__ == "__main__":
    run_eval(mode="hybrid", top_k=3)