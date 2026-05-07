from collections import defaultdict

from app.retrieval import ChunkRetriever
from app.llm import generate_answer, rewrite_query 
from app.query_preprocessing import clean_query_for_retrieval


def group_chunks_by_article(chunks):
    grouped = defaultdict(list)

    for chunk in chunks:
        grouped[chunk["url"]].append(chunk)

    articles = []
    for url, chunk_list in grouped.items():
        articles.append({
            "title": chunk_list[0]["title"],
            "url": url,
            "chunks": chunk_list,
        })

    return articles


def build_context(grouped_articles, max_chars=4000):
    parts = []

    for i, article in enumerate(grouped_articles, start=1):
        chunk_text = "\n\n".join(c["text"] for c in article["chunks"])

        part = (
            f"Kilde {i}\n"
            f"Titel: {article['title']}\n"
            f"URL: {article['url']}\n"
            f"Tekst:\n{chunk_text}"
        )
        parts.append(part)

    context = "\n\n---\n\n".join(parts)
    return context[:max_chars]

def answer_is_unknown(answer: str) -> bool:
    answer_lower = answer.lower()
    unknown_phrases = [
        "jeg ved det ikke",
        "det fremgår ikke",
        "ingen information",
        "ikke tydeligt fremgår",
    ]
    return any(phrase in answer_lower for phrase in unknown_phrases)

def ask(question: str, retriever: ChunkRetriever, top_k=5, mode="hybrid"):
    retrieval_query = clean_query_for_retrieval(question)

    retrieved = retriever.search(
        query=retrieval_query,
        top_k=top_k,
        mode=mode,
    )

    grouped_articles = group_chunks_by_article(retrieved)
    context = build_context(grouped_articles)

    answer = generate_answer(question, context)

    if answer_is_unknown(answer):
        rewritten_query = rewrite_query(question)
        cleaned_rewritten_query = clean_query_for_retrieval(rewritten_query)

        retrieved = retriever.search(
            query=cleaned_rewritten_query,
            top_k=top_k,
            mode=mode,
        )

        grouped_articles = group_chunks_by_article(retrieved)
        context = build_context(grouped_articles)

        answer = generate_answer(question, context)

        if answer_is_unknown(answer):
            return {
                "question": question,
                "answer": "Jeg ved det ikke. Jeg kan ikke finde relevant information i de tilgængelige kilder.",
                "sources": [],
                "retrieval_query": retrieval_query,
                "rewritten_query": rewritten_query,
            }

        return {
            "question": question,
            "answer": answer,
            "sources": [
                {
                    "title": article["title"],
                    "url": article["url"],
                }
                for article in grouped_articles
            ],
            "retrieval_query": cleaned_rewritten_query,
            "rewritten_query": rewritten_query,
        }

    return {
        "question": question,
        "answer": answer,
        "sources": [
            {
                "title": article["title"],
                "url": article["url"],
            }
            for article in grouped_articles
        ],
        "retrieval_query": retrieval_query,
    }