from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Chunk:
    chunk_id: str
    article_title: str
    url: str
    author: str | None
    updated: str | None
    text: str
    chunk_index: int
    paragraph_start: int
    paragraph_end: int


def split_paragraphs(content: str) -> list[str]:
    """
    splitting on newlines and stripping whitespace. Also removes empty paragraphs.
    """
    if not content:
        return []

    paragraphs = [p.strip() for p in content.split("\n")]
    paragraphs = [p for p in paragraphs if p]
    return paragraphs


def chunk_paragraphs(
    paragraphs: list[str],
    max_chars: int = 1200,
    overlap_paragraphs: int = 1,
) -> list[tuple[str, int, int]]:
    """
    Combine consecutive paragraphs into chunks up to max_chars.
    Returns:
        [(chunk_text, start_paragraph_idx, end_paragraph_idx), ...]
    """
    chunks: list[tuple[str, int, int]] = []

    i = 0
    n = len(paragraphs)

    while i < n:
        current_parts: list[str] = []
        current_len = 0
        start_idx = i
        j = i

        while j < n:
            paragraph = paragraphs[j]
            added_len = len(paragraph) + (2 if current_parts else 0)

            if current_parts and current_len + added_len > max_chars:
                break

            current_parts.append(paragraph)
            current_len += added_len
            j += 1

        if not current_parts:
            # fallback if one paragraph is extremely long
            paragraph = paragraphs[i]
            current_parts = [paragraph[:max_chars]]
            j = i + 1

        chunk_text = "\n\n".join(current_parts).strip()
        end_idx = j - 1
        chunks.append((chunk_text, start_idx, end_idx))

        if j >= n:
            break

        i = max(j - overlap_paragraphs, i + 1)

    return chunks


def build_chunks_from_articles(
    articles: list[dict],
    max_chars: int = 1200,
    overlap_paragraphs: int = 1,
    include_title: bool = True,
) -> list[Chunk]:
    all_chunks: list[Chunk] = []

    for article_idx, article in enumerate(articles):
        title = article.get("title", "")
        url = article.get("url", "")
        author = article.get("author")
        updated = article.get("updated")
        content = article.get("content", "")

        paragraphs = split_paragraphs(content)
        paragraph_chunks = chunk_paragraphs(
            paragraphs,
            max_chars=max_chars,
            overlap_paragraphs=overlap_paragraphs,
        )

        for chunk_idx, (chunk_text, p_start, p_end) in enumerate(paragraph_chunks):
            if include_title and title:
                text_for_embedding = f"{title}\n\n{chunk_text}"
            else:
                text_for_embedding = chunk_text

            all_chunks.append(
                Chunk(
                    chunk_id=f"article_{article_idx}_chunk_{chunk_idx}",
                    article_title=title,
                    url=url,
                    author=author,
                    updated=updated,
                    text=text_for_embedding,
                    chunk_index=chunk_idx,
                    paragraph_start=p_start,
                    paragraph_end=p_end,
                )
            )

    return all_chunks


def chunks_to_texts(chunks: list[Chunk]) -> list[str]:
    return [chunk.text for chunk in chunks]


def build_prompt_context(chunks: list[Chunk], max_chars: int = 4000) -> str:
    """
    Build final context for the LLM after retrieval.
    """
    parts = []

    for chunk in chunks:
        parts.append(
            f"Titel: {chunk.article_title}\n"
            f"URL: {chunk.url}\n"
            f"Tekst:\n{chunk.text}"
        )

    context = "\n\n---\n\n".join(parts)
    return context[:max_chars]