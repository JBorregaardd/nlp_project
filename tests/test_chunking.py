from app.chunking import split_paragraphs, build_chunks_from_articles


def test_split_paragraphs_removes_empty_lines_and_strips_whitespace():
    content = " Første afsnit \n\nAndet afsnit\n   \n Tredje afsnit "

    result = split_paragraphs(content)

    assert result == ["Første afsnit", "Andet afsnit", "Tredje afsnit"]


def test_build_chunks_from_articles_includes_title_and_metadata():
    articles = [
        {
            "title": "Forkølelse",
            "url": "https://example.com/forkolelse",
            "author": "Sundhed.dk",
            "updated": "2026-01-01",
            "content": "Forkølelse giver hoste.\nDet går ofte over af sig selv.",
        }
    ]

    chunks = build_chunks_from_articles(
        articles=articles,
        max_chars=1200,
        overlap_paragraphs=0,
        include_title=True,
    )

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.chunk_id == "article_0_chunk_0"
    assert chunk.article_title == "Forkølelse"
    assert chunk.url == "https://example.com/forkolelse"
    assert chunk.author == "Sundhed.dk"
    assert chunk.updated == "2026-01-01"
    assert chunk.text.startswith("Forkølelse")
    assert "Forkølelse giver hoste." in chunk.text