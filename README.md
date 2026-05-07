# Project Title
Grounded Medical Question Answering using Retrieval-Augmented Generation over Official Danish Health Sources

---

# 1. Project Description

This project aims to develop a medical question-answering system that provides reliable, evidence-based answers using only official Danish health information.

Recent trends show that users increasingly rely on AI-generated answers instead of consulting trusted platforms such as sundhed.dk. While AI systems are convenient, they are not guaranteed to use verified sources and may produce incorrect or misleading information. In the medical domain, this can have serious consequences.

To address this, the system will use Retrieval-Augmented Generation (RAG) to ensure that all answers are grounded in authoritative sources. The system retrieves relevant documents and generates answers based only on the retrieved content, improving reliability and transparency.

The system will be implemented as a dockerized FastAPI web service.

---

# 2. Tools and Methods

The project will use methods and tools covered in the course:

- **Web scraping and text processing**
  - Extraction of text from HTML pages
  - Cleaning and structuring of documents

- **Information Retrieval**
  - Sparse retrieval using TF-IDF
  - Dense retrieval using embeddings
  - Optional hybrid retrieval combining both approaches

- **Retrieval-Augmented Generation (RAG)**
  - Combining retrieved documents with an LLM to generate answers
  - Prompt engineering to ensure grounded responses

- **Web Service and Deployment**
  - FastAPI for API implementation
  - Docker for containerization

- **Evaluation**
  - Qualitative evaluation of answer quality and groundedness

---

# 3. Data

The dataset consists of articles from sundhed.dk Patienthåndbogen.

To ensure a manageable scope, the project focuses on a subset:

- Domain: **Virusinfektioner (viral infections)**
- Source: Official medical articles intended for patients
- Size: Approximately 15–20 documents

The data is collected by scraping publicly available HTML pages, followed by:

- Text extraction and cleaning
- Removal of non-content elements (navigation, metadata, footer)
- Splitting into smaller text chunks for retrieval

Each document includes metadata such as title, source, and update date.

---

# 4. API Description

The system will expose a REST API using FastAPI.

### `/v1/search`
- Input: natural-language query
- Output: top-k relevant document chunks based on retrieval

### `/v1/ask`
- Input: natural-language question
- Output: generated answer based on retrieved documents

The `/v1/ask` endpoint implements the full RAG pipeline:
1. Retrieve relevant document chunks
2. Construct a prompt using retrieved content
3. Generate an answer using an LLM

The system will be deployed as a Docker container.