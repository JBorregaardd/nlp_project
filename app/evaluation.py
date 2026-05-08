import json
from pathlib import Path

from app.ask import ask


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


def keyword_matches(answer: str, expected_keywords: list[str]) -> dict:
    answer_norm = normalize(answer)

    matched_keywords = []
    missed_keywords = []

    for keyword in expected_keywords:
        if normalize(keyword) in answer_norm:
            matched_keywords.append(keyword)
        else:
            missed_keywords.append(keyword)

    if not expected_keywords:
        coverage = 0.0
    else:
        coverage = len(matched_keywords) / len(expected_keywords)

    return {
        "coverage": coverage,
        "matched_keywords": matched_keywords,
        "missed_keywords": missed_keywords,
    }


def answer_is_unknown(answer: str) -> bool:
    answer_norm = normalize(answer)
    return any(phrase in answer_norm for phrase in UNKNOWN_PHRASES)


def evaluate_item(item, retriever, mode="hybrid", top_k=3):
    result = ask(
        question=item["question"],
        retriever=retriever,
        top_k=top_k,
        mode=mode,
    )

    answer = result.get("answer", "")
    sources = result.get("sources", [])

    expected_behavior = item.get("expected_behavior", "answer_from_context")
    expected_unknown = expected_behavior == "unknown"
    predicted_unknown = answer_is_unknown(answer)
    unknown_correct = predicted_unknown == expected_unknown

    retrieval_hit = source_hit(sources, item)

    expected_keywords = item.get("expected_keywords", [])
    keyword_result = keyword_matches(
        answer=answer,
        expected_keywords=expected_keywords,
    )

    return {
        "id": item["id"],
        "category": item["category"],
        "question": item["question"],
        "expected_behavior": expected_behavior,
        "expected_source_title": item.get("expected_source_title"),
        "acceptable_source_titles": item.get("acceptable_source_titles", []),
        "retrieval_hit": retrieval_hit,
        "keyword_coverage": keyword_result["coverage"],
        "expected_keywords": expected_keywords,
        "matched_keywords": keyword_result["matched_keywords"],
        "missed_keywords": keyword_result["missed_keywords"],
        "expected_unknown": expected_unknown,
        "predicted_unknown": predicted_unknown,
        "unknown_correct": unknown_correct,
        "answer": answer,
        "sources": sources,
        "retrieval_query": result.get("retrieval_query"),
        "rewritten_query": result.get("rewritten_query"),
    }


def run_eval(retriever, mode="hybrid", top_k=3, limit=None):
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))

    if limit is not None:
        questions = questions[:limit]

    results = []

    for item in questions:
        try:
            result = evaluate_item(
                item=item,
                retriever=retriever,
                mode=mode,
                top_k=top_k,
            )
        except Exception as exc:
            result = {
                "id": item.get("id"),
                "category": item.get("category"),
                "question": item.get("question"),
                "error": str(exc),
            }

        results.append(result)

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
        r["unknown_correct"]
        for r in results
        if "error" not in r and r.get("unknown_correct") is not None
    ]

    return {
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