# AskTube Requirements Document

Version: 0.2
Date: 2025-11-18

## Overview
AskTube converts YouTube video content (or provided transcripts) into structured learning materials (summary, detailed notes, mind map, enhanced PDF/HTML) and provides an interactive chat interface. RAG is implemented locally using FAISS with SentenceTransformers embeddings (all-MiniLM-L6-v2), with optional future migration to MongoDB for persistence.

## Backend API (FastAPI) — Current Status

- FastAPI app lives under `backend/app` with versioned routes at `/api/v1`.
- Interactive docs are at `/api/docs` (Swagger) and `/api/redoc` (ReDoc).
- OpenAPI spec is at `/api/openapi.json`.
- MongoDB connection uses Motor with ping + retry; configuration is loaded from `backend/.env`.
- Dev defaults: `MONGODB_URI=mongodb://localhost:27017`, `MONGODB_DB_NAME=AskTube`.

### How to Run (Windows PowerShell)

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
# Docs:  http://127.0.0.1:8000/api/docs
# Health: http://127.0.0.1:8000/api/v1/health
# Ready:  http://127.0.0.1:8000/api/v1/ready
```

Notes:
- Seeing `{ "detail": "Not Found" }` at `/` or `/docs` is expected; use the prefixed paths under `/api/...`.
- For deployment, override `MONGODB_URI` with your hosted connection string (e.g., Atlas `mongodb+srv://...`).

---

## Progress Summary

| Category | Completed | Total | Percent |
|----------|-----------|-------|---------|
| Core User Features | 6 | 9 | 66% |
| Chat Enhancements | 2 | 5 | 40% |
| Persistence & Storage | 1 | 7 | 14% |
| RAG Integration | 5 | 6 | 83% |
| Tooling / DX / Docs | 0 | 7 | 0% |
| Testing & Quality | 0 | 5 | 0% |
| Future Learning Features | 0 | 4 | 0% |

Legend: Completed items are implemented & smoke tested; partial means in progress or design locked.

---
## User Perspective Requirements
### Primary Use Cases
1. Provide a YouTube URL and receive:
   - Transcript files (JSON, plain text, timestamped)
   - Summary (concise overview)
   - Detailed structured notes (JSON + Markdown)
   - Mind map (Mermaid syntax)
   - Enhanced PDF/HTML bundle (optional)
2. Provide an existing transcript file and generate same outputs.
3. Interactively ask questions about the video content in a chat interface.
4. (Planned) Ask context-aware questions powered by semantic retrieval for large transcripts.
5. (Planned) Generate study aids like quizzes and flashcards.

### User Experience Requirements
| ID | Requirement | Status |
|----|-------------|--------|
| U1 | Simple CLI invocation with minimal flags | ✅ |
| U2 | Ability to skip individual outputs (summary/notes/mindmap) | ✅ |
| U3 | Optional PDF generation when summary & notes exist | ✅ |
| U4 | Caching to avoid repeated LLM costs per video | ✅ |
| U5 | Fast local LLM option (Ollama) | ✅ |
| U6 | Cloud LLM option (Gemini) | ✅ (legacy, still supported) |
| U7 | Interactive chat about transcript | ✅ (basic prompt stuffing) |
| U8 | Retrieval-based accurate answers with cited chunks | ✅ (local FAISS RAG) |
| U9 | Quiz / flashcard generation | ⏳ |
| U10 | Clear error messages for missing video ID / transcript | ✅ |
| U11 | Ability to specify model names | ✅ |
| U12 | Conversation history persistence | ✅ (file-based) |
| U13 | Conversation history storage in database | ⏳ |
| U14 | Performance acceptable for average video (<5 min pipeline) | ✅ (baseline) |

### Accessibility & Usability
| ID | Requirement | Status |
|----|-------------|--------|
| A1 | Outputs saved as plain text / markdown / HTML for easy viewing | ✅ |
| A2 | Minimal dependencies for base pipeline | ✅ |
| A3 | Works offline with Ollama (no Gemini requirement) | ✅ |
| A4 | Avoid vendor lock-in for embeddings | ⏳ (design supports flexible models) |

---
## Developer Perspective Requirements
### Functional Requirements
| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| F1 | Extract transcript from YouTube via `youtube-transcript-api` | ✅ | `transcript_extractor.py` |
| F2 | Save transcript in JSON, TXT, timestamped TXT | ✅ | |
| F3 | Generate summary with chunking & final consolidation | ✅ | `summary_generator.py` |
| F4 | Generate detailed notes with robust JSON extraction | ✅ | `detail_explanation_generator.py` |
| F5 | Generate mind map in Mermaid syntax | ✅ | `mindmap_generator.py` |
| F6 | Produce enhanced PDF/HTML with style & sections | ✅ | `pdf_exporter.py` |
| F7 | File-based cache with TTL per namespace | ✅ | `cache_manager.py` |
| F8 | Chat interface with backend abstraction | ✅ | `conversation_manager.py` refactored |
| F9 | Support multiple LLM backends (Ollama, Gemini) | ✅ | `llm_backend.py` |
| F10 | Add backend auto-selection | ⏳ | Planned improvement |
| F11 | Config layer using pydantic-settings | ✅ | `config.py` with `.env` (extra keys ignored) |
| F12 | Persistence abstraction interface | ⏳ | To create (file vs Mongo) |
| F13 | MongoDB storage for conversations | ⏳ | |
| F14 | Transcript chunking (token-aware heuristic) | ✅ | `rag_chunker.py` |
| F15 | Embedding generation (SentenceTransformers / Ollama) | ✅ | `rag_embeddings.py` (all-MiniLM-L6-v2, dim=384) |
| F16 | Vector storage (MongoDB Atlas Vector) | 🔁 | Using FAISS locally now (`rag_faiss_store.py`) |
| F17 | Retrieval + prompt construction with citations | ✅ | `conversation_manager.py` RAG builder |
| F18 | Re-index logic based on transcript hash | ✅ | `rag_indexer.py` |
| F19 | Quiz generation module | ⏳ | |
| F20 | CLI cache management operations | ⏳ | |
| F21 | Structured logging replacing prints | ⏳ | |

### Non-Functional Requirements (NFR)
| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| N1 | Modular architecture (independent generators) | ✅ | Clear separation |
| N2 | Extensible backend support (add new LLM easily) | ✅ | `LLMBackend` ABC |
| N3 | Resilient parsing of LLM JSON outputs | ✅ | Multiple repair strategies |
| N4 | Deterministic outputs for identical inputs when cached | ✅ | Cache keyed by video/model |
| N5 | Efficient handling of long transcripts (chunking) | ✅ (summary/notes) / ⏳ (RAG indexing) | |
| N6 | Minimal disk footprint for cached artifacts | ✅ | TTL & namespaces |
| N7 | Graceful degradation if PDF library missing | ✅ | Falls back to HTML |
| N8 | Horizontal scalability via DB (future state) | ⏳ | Pending Mongo integration |
| N9 | Observability (logs, metrics) | ⏳ | Logging planned |
| N10 | Security: no external exposure of API keys in logs | ✅ | Explicit error messages only |

### RAG Roadmap Requirements
| ID | Requirement | Status |
|----|-------------|--------|
| R1 | Chunk transcript into overlapping segments | ✅ |
| R2 | Generate embeddings per chunk | ✅ |
| R3 | Store embeddings + metadata in vector collection | ✅ (FAISS + JSON metadata) |
| R4 | Query embedding for user question and get top-k chunks | ✅ |
| R5 | Build prompt from retrieved chunks + short history | ✅ |
| R6 | Append chunk citations to answer | ✅ |
| R7 | Rebuild index only if transcript hash changes | ✅ |

### Future Learning Features
| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| L1 | Quiz generator (MCQ) from notes & transcript | ⏳ | |
| L2 | Flashcard generator (Q/A pairs) | ⏳ | |
| L3 | Summary comparison (diff between runs) | ⏳ | |
| L4 | Mind map export as image (optional) | ⏳ | Possible via mermaid CLI |

---
## Environment Variables (Current & Planned)
| Variable | Purpose | Required | Example |
|----------|---------|----------|---------|
| GOOGLE_API_KEY | Gemini backend key | Optional | `AIza...` |
| MONGODB_URI | MongoDB connection string (local or hosted) | Current | `mongodb://localhost:27017` or `mongodb+srv://user:pass@cluster/...` |
| MONGODB_DB_NAME | Database name | Current | `AskTube` |
| ALLOWED_ORIGINS | Frontend origin(s), comma-separated | Current | `http://localhost:5173` |
| MONGO_VECTOR_COLLECTION | Vector chunk collection | Planned | `transcript_chunks` |
| MONGO_CONVERSATIONS_COLLECTION | Conversation history collection | Planned | `conversations` |
| EMBEDDING_MODEL | Embedding model identifier | Current | `sentence-transformers/all-MiniLM-L6-v2` |
| USE_RAG | Enable retrieval in chat | Current | `true`/`false` |
| CHUNK_TOKEN_TARGET | Approx tokens per chunk | Current | `220` |
| CHUNK_OVERLAP | Overlap tokens | Current | `40` |
| TOP_K | Retrieval top-k results | Current | `5` |
| FAISS_INDEX_PATH | FAISS index file path | Current | `vector_store/faiss.index` |
| FAISS_META_PATH | FAISS metadata JSON path | Current | `vector_store/metadata.json` |
| VECTOR_INDEX_NAME | Atlas vector index name | Planned | `vector_index` |
| LOG_LEVEL | Logging verbosity | Planned | `info` |

---
## Data Models (Planned / Existing)
### Transcript Chunk (RAG)
```
{
  text: str,
  embedding: List[float],  # length = 384 (MiniLM)
  metadata: {
    video_id: str,
    chunk_id: int,
    token_estimate: int
  },
  created_at: ISODate
}
```

### Conversation Document (Future Mongo)
```
{
  user_id: str,
  video_id: str,
  messages: [ { role: 'user'|'assistant', content: str, timestamp: ISODate } ],
  transcript: str | null,
  created_at: ISODate,
  updated_at: ISODate
}
```

### Notes JSON Schema
```
{
  summary: str,
  detailed_notes: str,
  key_concepts: str,
  examples: str,
  memory_tricks: str,
  common_mistakes: str,
  sticky_notes: str
}
```

---
## Open Questions / Decisions
| Topic | Question | Pending Action |
|-------|----------|----------------|
| Embeddings | Use local Ollama embedding model or MiniLM long-term? | Using MiniLM now; configurable via `EMBEDDING_MODEL` |
| Vector Index | Create Atlas index manually or provide script? | Using FAISS locally; Atlas plan deferred |
| Persistence | Migrate chat history to Mongo immediately? | Decide priority vs RAG work |
| Transcript Hash | Use SHA-256 for re-index detection? | Implement in indexing module |
| Quiz Generation | Which format (MCQ JSON schema)? | Define schema before implementation |
| Logging | Use `logging` with JSON format or plaintext? | Choose format for observability |

---
## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Large transcripts may exceed prompt limits (no retrieval yet) | Inaccurate/slow responses | Implement RAG chunk retrieval (planned) |
| JSON generation occasionally malformed | Breaks downstream parsing | Existing robust repair + add pydantic validation |
| Local model performance on very long texts | Latency | Parallel chunk processing + retrieval narrowing |
| Atlas index mismatch dimension | Retrieval failure | Enforce dimension = 384 in config validation |
| Duplicate re-indexing | Wasted compute | Transcript hash check & skip |

---
## Implementation Roadmap (Next Sprints)
1. Structured logging middleware (request IDs, latency, error capture) for the API.
2. Persistence abstraction + file backend adapter.
3. Mongo persistence for conversations (optional, behind a flag).
4. API smoke tests: `/health`, `/ready`, `/chat`, `/process` (LLM/Mongo mocked).
5. Documentation & diagrams (RAG flow, CLI flags, API quick start).
6. Optional Docker Compose for local Mongo and API.
7. Extended test coverage (RAG retrieval correctness, persistence, CLI).

---
## Acceptance Criteria (Selected)
| Feature | Criteria |
|---------|----------|
| Summary Generation | For a >10k char transcript, summary completes with chunk merge and <300 words total |
| Notes JSON | Returns all schema fields non-empty (unless content truly absent) and passes validation |
| Mind Map | Outputs valid Mermaid starting with `mindmap` and max depth <=4 |
| PDF Export | Generates either PDF (if weasyprint available) or HTML fallback with all sections |
| Chat (Basic) | Answers limited to transcript content; prompts show transcript truncation boundary |
| Chat (RAG) | Returns answers referencing retrieved chunks with at least one citation or states not found |
| Re-index | Skips when transcript hash unchanged |

---
## Completed vs Pending Checklist
### Completed
- [x] Transcript extraction
- [x] Multi-format transcript saving
- [x] Summary generation with chunking
- [x] Detailed notes (robust JSON parsing)
- [x] Mind map generation
- [x] PDF/HTML export styling
- [x] Caching system
- [x] LLM backend abstraction
- [x] Chat prompt stuffing version
- [x] Config module (`config.py`) with `.env`
- [x] RAG indexing (chunk → embed → FAISS)
- [x] RAG retrieval in chat with citations
- [x] Chat CLI auto-index + `--use-rag` / `--no-rag` / `--force-reindex`

### In Progress / Pending
- [ ] Persistence backend interface
- [ ] Mongo conversation persistence
- [ ] Structured logging
- [ ] Quiz / flashcard generator
- [ ] CLI enhancements (cache ops, backend auto)
- [ ] Tests for new layers (persistence, RAG, logging)
- [ ] README architecture update

---
## Change Log
| Date | Change | Author |
|------|--------|--------|
| 2025-11-18 | Initial comprehensive requirements document | Copilot Assistant |

---
## Next Action
Prioritize: Add API logging middleware and smoke tests; finalize persistence abstraction design; document API quick start and `/api/docs` usage in README.

---
## Quick Start (Backend API)

- Install and run API:
  ```powershell
  cd backend
  python -m pip install -r requirements.txt
  python -m uvicorn app.main:app --reload
  ```

- Open docs and health:
  - Swagger UI: `http://127.0.0.1:8000/api/docs`
  - ReDoc: `http://127.0.0.1:8000/api/redoc`
  - Health: `http://127.0.0.1:8000/api/v1/health`
  - Ready:  `http://127.0.0.1:8000/api/v1/ready`

---
## Quick Start (Chat with RAG)

- Install dependencies:
  ```powershell
  C:\Users\chava\Desktop\Projects\asktube\.venv\Scripts\python.exe -m pip install -r requirements.txt
  ```

- Ensure Ollama is running and model is available:
  ```powershell
  ollama pull qwen2.5:7b
  ```

- Chat from a URL (auto-fetch transcript, auto-index for RAG):
  ```powershell
  C:\Users\chava\Desktop\Projects\asktube\.venv\Scripts\python.exe chat_cli.py "https://www.youtube.com/watch?v=GuyZspG3-Po" --backend ollama --model qwen2.5:7b --use-rag
  ```

- Optional: force re-index if transcript changed:
  ```powershell
  C:\Users\chava\Desktop\Projects\asktube\.venv\Scripts\python.exe chat_cli.py "https://www.youtube.com/watch?v=GuyZspG3-Po" --backend ollama --model qwen2.5:7b --use-rag --force-reindex
  ```
