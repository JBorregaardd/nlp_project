# Sundhed.AI
A Medical Question Answering system using Retrieval-Augmented Generation over Patienthåndbogen

---

# 1. Project Description

This project develops a Danish medical question-answering system that aims to provide grounded, evidence-based answers using articles from Sundhed.dk’s Patienthåndbogen about virus infections.

The project is motivated by the increasing use of AI-generated answers instead of trusted health platforms such as Sundhed.dk. While AI systems are convenient, they are not guaranteed to use verified sources and may produce incorrect or misleading information. In the medical domain, this can have serious consequences. This concern is reflected in recent Danish media coverage describing how fewer users visit health information platforms after the introduction of AI-generated search summaries. Source: https://www.dr.dk/nyheder/indland/faerre-besoeger-sundhedsplatform-efter-udbredelse-af-googles-ai-oversigt

To address this problem, the system uses Retrieval-Augmented Generation (RAG). Instead of relying only on the language model’s internal knowledge, the system first retrieves relevant passages from a curated collection of Danish Sundhed.dk articles. The language model then generates an answer based only on the retrieved context, improving transparency and reducing the risk of unsupported answers.

The system is evaluated using a small manually constructed test set of Danish questions. The test set covers factual questions, symptom-based questions, diagnosis-like questions, and out-of-scope questions. The evaluation measures whether the system retrieves relevant sources, includes expected keywords in the generated answers, and correctly refuses to answer questions that are not covered by the available data.

The system is implemented as a dockerized FastAPI web service with endpoints for question answering, and evaluation, together with a simple browser-based frontend.

## Repository Structure

```text
app/
  main.py                  FastAPI application and API endpoints
  ask.py                   Main RAG question-answering logic
  retrieval.py             Sparse, dense, and hybrid retrieval
  embed.py                 Embedding utilities and cache handling
  llm.py                   LLM calls, prompting, and query rewriting
  query_preprocessing.py   Danish query preprocessing
  chunking.py              Article chunking
  evaluation.py            Backend evaluation logic
  static/                  Browser-based frontend

data/
  raw/                     Raw scraped links
  processed/               Processed Sundhed.dk article dataset

evaluation/
  questions.json           Manually constructed evaluation questions
  run_eval.py              Standalone evaluation script
  results_*.json           Saved evaluation results

scrape_scripts/
  collect_links.py         Collects relevant Sundhed.dk article URLs
  scrape_articles.py       Scrapes and processes article content
  utils.py                 Shared scraping utilities
  scrape_config.py         Scraping configuration

tests/
  test_api.py              API tests
  test_chunking.py         Chunking tests
  test_embed.py            Embedding/cache tests
  test_retrieval.py        Retrieval tests

Dockerfile                 Docker configuration
requirements.txt           Python dependencies
README.md                  Project documentation
```

---

# 2. Tools and Methods

The project uses the following course-related methods and tools:

- **Text processing:** scraping, cleaning, chunking, and Danish query preprocessing
- **Information retrieval:** TF-IDF retrieval, embedding-based retrieval, and hybrid retrieval
- **RAG:** retrieved Sundhed.dk chunks are used as grounded context for LLM answer generation
- **LLM integration:** OpenAI Python client with an OpenAI-compatible CampusAI API
- **Web service:** FastAPI backend, Docker deployment, and a simple browser-based frontend
- **Testing and evaluation:** pytest unit tests and a manually constructed Danish evaluation dataset

---

# 3. Data

The dataset consists of Danish patient-facing articles from **Sundhed.dk Patienthåndbogen**.

To keep the project scope manageable, the system focuses on one medical subdomain:

- **Domain:** Virusinfektioner, viral infections
- **Source:** Sundhed.dk Patienthåndbogen
- **Language:** Danish
- **Format:** Processed JSONL file
- **Size:** 17 articles

The processed dataset is stored as JSONL, where each line represents one article with source metadata and cleaned article text.

Fields:

`url`, `title`, `author`, `role`, `updated`, `source`, `domain`, `container`, `content`

Example:

```json
{
  "url": "https://www.sundhed.dk/...",
  "title": "Forkølelse",
  "author": "Lene Fogt Lundbo",
  "role": "Afdelingslæge",
  "updated": "27.02.2024",
  "source": "sundhed.dk",
  "domain": "virusinfektioner",
  "container": "main",
  "content": "Forkølelse er en infektion i de øvre luftveje..."
}
```

The `content` field contains the cleaned article body. During preprocessing, each article is split into smaller overlapping chunks used as retrieval units in the RAG pipeline. Each chunk keeps metadata such as the original article title and URL, so generated answers can be traced back to their sources.

The dataset is included in the repository under:

```text
data/processed/virusinfektioner_articles.jsonl
```

---

# 4. System Architecture

The system is implemented as a Retrieval-Augmented Generation (RAG) web service. It consists of four main parts: data preprocessing, retrieval, answer generation, and evaluation.

```text
Sundhed.dk articles
→ cleaning and chunking
→ sparse / dense / hybrid retrieval index
→ user question
→ query preprocessing: cleanup + Danish stopword removal
→ top-k retrieved chunks
→ grounded context construction
→ LLM answer generation
→ answer with source references
```

The main endpoint is `/v1/ask`, which runs the full RAG pipeline: question preprocessing, retrieval of relevant article chunks, context construction, and LLM-based answer generation.

The system supports `sparse`, `dense`, and `hybrid` retrieval using TF-IDF, CampusAI embeddings, or a combination of both. The LLM is called through the OpenAI Python client and is prompted to answer only from the retrieved context, keep answers concise, cite source titles, and avoid definite diagnoses.

If the first retrieval does not provide enough context, the system rewrites the question into a shorter medical search query and retries retrieval. If no supported answer is found, it returns “jeg ved det ikke”.

The `/v1/evaluate` endpoint runs the evaluation dataset and reports source hit rate, keyword coverage, and unknown-answer accuracy. The frontend supports both question answering and evaluation inspection.

---

# 5. How to Run

## 5.1 Environment variables

The system uses an OpenAI-compatible API through CampusAI. API keys are not included in the repository and must be provided in a `.env` file in the project root:

```env
CAMPUSAI_API_KEY=your_api_key_here
CAMPUSAI_API_URL=https://api.campusai.compute.dtu.dk/v1
CAMPUSAI_MODEL=Gemma 4
CAMPUSAI_EMBED_MODEL=Nomic Embed Text
```

Optional data paths:

```env
ARTICLES_PATH=data/processed/virusinfektioner_articles.jsonl
EMBED_CACHE_PATH=data/cache/chunk_embeddings.npy
```

## 5.2 Run locally

Install dependencies and start the FastAPI server:

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open the frontend:

```text
http://127.0.0.1:8000
```

API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## 5.3 Run with Docker

Build and run the Docker container:

```bash
docker build -t sundhed-ai .
docker run --rm -p 8000:8000 --env-file .env sundhed-ai
```

Then open:

```text
http://127.0.0.1:8000
```

---

# 6. API Documentation

The FastAPI application exposes the following main endpoints.

## `GET /health`

Health check endpoint.

Example response:

```json
{
  "status": "ok"
}
```

## `POST /v1/ask`

Runs the full RAG pipeline for a Danish user question.

Example request:

```json
{
  "question": "Hvad er forkølelse?",
  "top_k": 5,
  "mode": "hybrid"
}
```

Parameters:

- `question`: Danish user question
- `top_k`: number of retrieved chunks, between 1 and 10
- `mode`: retrieval mode, one of `sparse`, `dense`, or `hybrid`

Example response fields:

```json
{
  "question": "Hvad er forkølelse?",
  "answer": "Forkølelse er en infektion i de øvre luftveje...",
  "sources": [
    {
      "title": "Forkølelse",
      "url": "https://www.sundhed.dk/..."
    }
  ],
  "retrieval_query": "forkølelse?",
  "rewritten_query": null
}
```

## `POST /v1/evaluate`

Runs the evaluation dataset through the RAG system.

Example request:

```json
{
  "top_k": 3,
  "mode": "hybrid",
  "limit": null
}
```

Parameters:

- `top_k`: number of retrieved chunks
- `mode`: retrieval mode, one of `sparse`, `dense`, or `hybrid`
- `limit`: optional number of evaluation questions to run

Example response fields:

```json
{
  "mode": "hybrid",
  "top_k": 3,
  "num_questions": 28,
  "num_in_scope": 24,
  "num_out_of_scope": 4,
  "retrieval_hit_rate": 1.0,
  "avg_keyword_coverage": 0.884,
  "unknown_accuracy": 1.0
}
```

---

# 7. Testing

The project includes unit tests for core components of the system. The tests cover chunking, retrieval, embedding/cache behavior, and API behavior.

Run the tests with:

```bash
python -m pytest
```

The tests are intended to verify that the main components of the RAG pipeline behave as expected and that the FastAPI application can be initialized and called.

---

# 8. Evaluation and Results

The system is evaluated using a manually constructed Danish test set with 28 questions. The dataset contains 24 in-domain questions and 4 out-of-scope questions.

The questions cover:

- factual questions
- symptom-based questions
- diagnosis-like questions
- treatment and vaccination questions
- out-of-scope medical and non-medical questions

The evaluation measures three aspects:

- **Source hit rate:** whether the expected or acceptable source article is retrieved
- **Keyword coverage:** how many manually selected expected keywords appear in the generated answer
- **Unknown accuracy:** whether the system correctly identifies when it can or cannot answer from the available sources

Final evaluation result:

| Setup | top_k | Source hit rate | Avg. keyword coverage | Unknown accuracy |
|---|---:|---:|---:|---:|
| Hybrid | 3 | 100.0% | 88.4% | 100.0% |

The evaluation can be run through the frontend or through the `/v1/evaluate` endpoint.

---

# 9. Limitations

The system has several limitations:

- **Limited dataset scope:** The system only uses a small subset of Sundhed.dk Patienthåndbogen articles about virus infections. It should therefore not be expected to answer questions about other medical domains such as diabetes, injuries, cancer, medication in general, or mental health.

- **Retrieval noise:** The retriever may sometimes return chunks from articles that are only weakly related to the question. The answer generation prompt is designed to reduce the impact of irrelevant context, but retrieval quality remains an important limitation.

- **Symptom wording and query mismatch:** User questions can describe symptoms in many different ways. For example, a user might write “kaste op”, while the source articles may use “opkast” or “opkastninger”. To address this, the system includes an LLM-based query rewriting fallback, where unsupported questions are rewritten into shorter medical search queries and retrieval is retried.

- **Danish-only system:** The current version is designed for Danish questions and Danish source articles. An extension to English questions would require either translation of user queries, bilingual retrieval, or answer generation that can translate from Danish source material into English. This was something i initially wanted to explore, but ended up not doing due to time constraints.

- **Not a diagnostic tool:** The system is intended for grounded information retrieval and question answering, not medical diagnosis. For symptom-based questions, it should only suggest what symptoms may be compatible with and should not replace professional medical advice.

---

# 10. AI Assistance Declaration

AI assistance was used during the development of this project.

Specifically, AI was used for:

- coding support and debugging during implementation
- drafting a frontend.
- generating and refining evaluation questions
- improving README wording and project documentation

All code, test questions, evaluation results, and final project decisions were reviewed, adapted, and verified by the author.