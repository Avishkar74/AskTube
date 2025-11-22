# Technical Requirements Document (TRD)

## Constraints

- Only Gemini API key (no other paid services)
- No mobile app
- No browser extension (initially)
- Optional/local-only features allowed (FAISS, file storage, etc.)

## Title

YouTube Learning Assistant (LangChain + Gemini + React)

## Overview (Synced with Implementation)

Single FastAPI backend exposes a unified processing pipeline (`POST /api/v1/process`) that produces transcript → summary → structured notes → mind map → HTML/PDF artifact, and supports chat/Q&A with optional semantic/timestamp RAG. Frontend (React + TypeScript) consumes reports, config, chat, and video introspection endpoints. Only Gemini is a paid dependency; all others are free/local.

## Objectives

- Convert YouTube content into high-quality learning artifacts.
- Enable conversational Q&A grounded in transcript content.
- Provide fallback when automatic transcript retrieval fails.
- Avoid paid services beyond Gemini.

## Out of Scope

- Mobile/PWA-specific native features.
- Browser extension.
- Paid vector DBs, hosted observability platforms, managed proxies.

## Functional Requirements (Reconciled)

### 1. Input & Transcript

- Accept YouTube URL; derive `video_id`.
- Fetch transcript (youtube-transcript-api); manual paste fallback (planned).
- Segment timing used for chunking in RAG.
- Implicit caching via index/artifact presence.

### 2. Unified Processing Pipeline (Implemented)

- `POST /api/v1/process` triggers background task: transcript → summary → notes → mind map → export HTML/PDF → GridFS store → report status update.
- Consolidates multiple generation steps for simpler MVP.

### 3. Learning Outputs

- Implemented: Summary, structured notes, mind map (Mermaid), HTML/PDF artifact.
- Planned: Memory aids, sticky notes, mind map rendered image.

### 4. Chat (RAG Optional)

- `POST /api/v1/chat` accepts `youtube_url` or `video_id` + `message`.
- Supports semantic top-k retrieval or timestamp window; returns citations.
- Conversation memory (userId+videoId) planned; current implementation stateless.

### 5. Retrieval Augmentation (Core Implemented)

- Local FAISS per video (segment-aware chunking, MiniLM embeddings).
- Semantic & timestamp queries; citations include chunk indices and start/end seconds.
- Auto-build during pipeline; potential force rebuild flag.

### 6. PDF/HTML Export

- HTML (or PDF fallback) stored in GridFS; downloaded via `/api/v1/reports/{id}/download`.
- Future inclusion: memory aids, sticky notes, rendered PNG of mind map.

### 7. Persistence

- Implemented: reports collection.
- Planned: transcripts cache, conversations store, file-based fallback adapter.

### 8. Security & Operations

- Secrets in environment (.env); never exposed client-side.
- CORS restricted; `X-Request-ID` exposed.
- Pydantic validation on models.
- Rate limiting (token bucket) planned.

### 9. Observability

- Loguru request logging middleware (request-id + latency).
- Structured logging enrichment (method/path/status/duration) planned.
- LangSmith tracing off by default.

## Non-Functional Requirements

- Performance: p95 < 2.5s for non-LLM cached endpoints; LLM latency dominates generation.
- Reliability: manual transcript fallback workflow planned.
- Cost: no paid services other than Gemini.
- Maintainability: modular services, typed schemas, clear README.

## System Architecture

**Frontend**: React + TS + Vite + Tailwind; components for URL input, summary, notes, memory aids (future), sticky notes (future), mind map, chat, PDF download.
**Backend Routers**: health/ready, reports (process/list/get/download + video rag/transcript/chunks), chat, config.
**Services**: transcript_service, processing_service, rag_store, chat_service, llm_backend, gridfs helpers.
**Planned Additions**: memory service, rate limiting middleware, file storage adapter.

## Architecture Overview

**Layering**: FastAPI routers (API contract) → Services (domain logic: processing, chat, RAG, transcript, LLM backends) → Repositories (Mongo persistence) → Infra (Mongo lifecycle, GridFS helpers, settings, logging middleware).

**Execution Model**: Synchronous request handlers for lightweight ops; heavy pipeline runs in a FastAPI `BackgroundTasks` thread (not async) while Mongo + GridFS access is async.

### 1. Transcript Acquisition

**Entry**: Processing pipeline (`process_report` in `processing_service.py`) calls `get_transcript_text` and `get_transcript_segments`.
**Segments** contain `(text, start, duration)` enabling timing-aware chunking for RAG. If segment fetch fails a warning is logged and pipeline continues with plain text only.
**Transcript text** is truncated only when used inside chat fallback; full text used for artifacts.
**No persistent transcript caching yet**—fetch is on-demand; caching implicitly occurs through existence of FAISS index and generated artifacts.

### 2. Chunking & RAG Index Build (`rag_store.py`)

**Two chunking strategies**:
- `_chunk_segments`: Accumulates segment texts until `chunk_chars` limit; chunk start = first segment start; chunk end = last segment end. Preserves temporal boundaries.
- `_chunk_text`: Greedy fixed-size slicing when segment metadata absent.
**Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`, converted to float32, normalized with L2 + epsilon for stability (avoids division by zero).
**Index**: FAISS `IndexFlatIP` (inner product). Because vectors are L2-normalized, inner product approximates cosine similarity.
**Storage**: Two files per `video_id`: `<video_id>.index` (FAISS binary) and `<video_id>.meta.json` (array of chunks with text + timing). Base path: `faiss`.
**Retrieval (semantic)**: Embed query → normalize → `index.search(k)` → map indices to chunk texts and timing.
**Retrieval (timestamp)**: Iterate to find containing chunk or nearest by start time, then window-expand neighbors.
**Results** packaged with `chunk_index`, `score` (semantic), `start_sec`, `end_sec`. Timestamp retrieval sets `score=None` since it’s positional, not similarity-based.

### 3. Processing Pipeline (`processing_service.py`)
**Flow**:

1.  Status to “running” (`report_repo.update_status`).
2.  Extract `video_id` from URL; fetch transcript and segments. Persist minimal video metadata (placeholder title).
3.  Attempt RAG index build (does not abort pipeline on failure—warns only).
4.  Generate summary, notes, mind map via external local modules (`summary_generator`, `detail_explanation_generator`, `mindmap_generator`). Lazy import prevents cold-start model penalty.
5.  PDF/HTML export via `EnhancedPDFExporter`: constructs a composite HTML with all artifacts; attempts PDF conversion. If PDF generation tool (WeasyPrint) fails, HTML remains primary artifact.
6.  GridFS upload (`upload_bytes`) with metadata `content_type`.
7.  Set artifacts: either `html_file_id` or `pdf_file_id` depending on produced extension.
8.  Status to “succeeded” or “failed” with captured exception message.

**Resilience**: Each step isolates failure; RAG build failure doesn’t kill artifact generation; transcript segment failure downgrades to text-only mode.

### 4. Report Lifecycle & Persistence (`report_repo.py`)

**Insert**: Creates document `{youtube_url, status=queued, artifacts={}, timestamps}`; returns `_id` as string.
**Status updates**: Atomically sets status, updated_at, and optional error.
**Artifacts**: Replace entire artifacts map (GridFS file IDs).
**Listing**: Filter optional `video_id`, sorted by `created_at` descending, offset/limit implemented via Mongo cursor ops (skip, limit).
**IDs**: Always stringified from native ObjectId for API transparency.

### 5. GridFS Artifact Storage (`gridfs.py`)

**Upload**: `bucket.upload_from_stream(filename, bytes, metadata={content_type})` returning ObjectId → string.
**Download**: Opens stream, reads until exhaustion accumulating bytes into bytearray. Provides uniform `FileNotFoundError` if absent (maps `gridfs.NoFile`).
**Streaming Response**: API currently buffers entire file then yields single chunk (`StreamingResponse(iter([data]))`). Could be optimized to stream chunk-by-chunk.

### 6. Chat & Q/A Flow (`chat_service.py`)
**Steps for each chat request**:

1.  Resolve `video_id` (chosen from explicit `video_id` or parsed from URL).
2.  Load transcript (truncated to 15k chars to keep prompt size manageable).
3.  Decide RAG usage: `payload.use_rag` override or global `settings.USE_RAG`; verify index existence.
4.  Timestamp detection: `_parse_timestamp_seconds` uses regex patterns for h:mm:ss, m:ss, human-readable X min Y sec, and Xm Ys forms. If found → timestamp retrieval with optional neighbor window. Else semantic retrieval using `retrieve(video_id, message, top_k=k)`.
5.  Construct prompt: System instruction + either RAG context (labeled `[cN]`) or transcript snippet. Grounding strategy instructs model to cite chunk tokens `[cN]`.
6.  Model selection: `auto_select_backend("ollama", model)` tries Ollama first; if failing, attempts Gemini. If both fail = transcript fallback generative stub.
7.  Response assembly: Citations array contains chunk metadata (including `start_sec`, `end_sec`) plus model meta (backend, fallback flag, retrieval params).

**Fallback logic**: If generation fails entirely and transcript exists, produce minimal heuristic answer; else disclaim inability.

### 7. LLM Backend Abstraction (`llm_backend.py`)

**OllamaBackend**: Validates installation by calling `ollama.list()`. Generation uses `ollama.generate` with optional `num_predict`; accepts dict or object result forms protecting against client variation.
**GeminiBackend**: Fetches API key from environment (multiple variable names tolerated), initializes LangChain wrapper `ChatGoogleGenerativeAI`. Implements exponential backoff for 429/resource exhaustion. Returns `.content` from LangChain message object.
**Auto Selection**: Sequence of preferred backend then alternate; `is_available()` checks environment readiness (Gemini key presence / Ollama service reachable).
**Error boundaries** ensure chat doesn’t crash if one backend is temporarily unreachable.

### 8. Config Exposure (`routes_config.py`, `config.py`)

Settings loaded once (cached singleton). `.env` located at `.env` via relative path calculation; supports dual naming (`MONGODB_` and `MONGO_` prefixes).
`GET /config` returns non-sensitive fields (`API_PREFIX`, `USE_RAG`, `ALLOWED_ORIGINS`, `exposed_headers`, `version`). No secrets, enabling dynamic frontend adaptation.

### 9. Health & Readiness (`routes_health.py`, `mongo.py`)

**Startup**: `init_mongo` performs up to 3 attempts with linear backoff; attaches `mongo_connected`, `mongo_error`, `db` onto `app.state`.
`/health`: Returns "ok" if `mongo_connected`; "degraded" otherwise, plus timestamp ISO8601 UTC using timezone-awareness.
`/ready`: Executes `list_collection_names()` to assert DB usability; returns readiness status.
**Shutdown**: Closes client, clears state.

### 10. Middleware & Observability

Request logging middleware (not shown in your snippet detail but referenced) typically: generates `X-Request-ID` (UUID), attaches to response headers, measures latency, logs structured line (to loguru).
CORS configured to expose `X-Request-ID` so frontend can correlate client actions with server logs.
Planned structured logging enrichment: add method, path, status, duration_ms, request_id consistently.

### 11. Data Paths & Isolation

FAISS & metadata under `faiss` separate from source tree—facilitates container volume mapping and retention policies.
GridFS artifacts stored inside Mongo database; IDs persisted in `reports.artifacts`.

### 12. Error Handling Strategy

**API route level**: wraps unexpected exceptions returning 500 with `detail=str(e)`.
**Pipeline**: Broad try/except ensures proper status flip to “failed” with captured error string—prevents silent job loss.
**RAG operations** intentionally fail-soft (warn and proceed with transcript-only answer).

### 13. Concurrency & Performance Considerations

`BackgroundTasks` run in threadpool separate from event loop; Mongo operations inside pipeline steps leverage motor’s async parts but some artifact steps (file I/O, PDF generation) are synchronous (potentially blocking). For heavy scale, these would migrate to Celery / separate worker process.
Embedding and FAISS building happen once per video per pipeline; retrieval is O(log n) in FAISS (flat IP: O(n) similarity but typically small n).
Prompt length controls: transcript truncated to cap memory footprint.

### 14. Security & Isolation

No secrets exposed via API responses; environment-only.
RAG index files are local; no remote network vector store attack surface.
Input validation via Pydantic ensures typed payloads; potential future hardened cleaning of YouTube URL (currently simple `split("v=")` extraction).

### 15. Extensibility Hooks (Planned)

**Conversation persistence**: add repository layer and service storing chat messages keyed by (user_id, video_id) with summarization to prevent context bloat.
**Rate limiting**: in-memory token bucket keyed by IP/request path; integrate into middleware before hitting routers.
**File-based persistence fallback**: implement interface `PersistenceBackend` with `MongoPersistence` & `FilePersistence` selection by config.

### 16. Failure Modes & Recovery

**Transcript unavailable**: Pipeline still produces partial artifacts (may degrade quality); chat falls back to limited transcript or disclaimers.
**Ollama down**: Auto-select attempts Gemini; if Gemini unavailable, fallback answer stub prevents HTTP 500.
**FAISS index corrupt/missing**: RAG retrieval returns empty list; chat reverts to transcript path automatically.
**GridFS upload failure**: Sets status “failed” with error; artifact IDs remain absent, enabling frontend retry UX.

### 17. Citations & Timestamp Navigation

**Citation mapping**: Each retrieved chunk labeled `[cN]` in prompt; returned JSON citation includes `chunk_index` for UI direct linking, plus `start_sec`/`end_sec` for timeline highlighting or future “jump to time” feature.
**Timestamp parsing** resilient to multiple formats increasing UX flexibility in chat queries.

### 18. Configuration & Feature Flagging

`USE_RAG` globally toggles retrieval usage if request doesn’t override. Allows rapid disabling for performance/testing.
Future: add discrete flags for `USE_GEMINI_FOR_SUMMARIES`, `ENABLE_CONVERSATION_MEMORY`, `ENABLE_RATE_LIMITING`.

### 19. Data Integrity Notes

Report document updates use `$set` ensuring partial field updates; no atomic multi-document operations needed yet.
No transaction usage; operations single-document, acceptable for current consistency requirements (pipeline steps idempotent if re-run with same report id except duplicates of artifacts—handled externally).

### 20. Key Algorithms (Simplified)

**Chunking with segments**: accumulate until character limit; flush with combined text and timing.
**Timestamp retrieval**: linear search to find containing chunk; fallback to nearest start time; window expansion for context.
**Embedding normalization**: vector / (||vector|| + 1e-12) for numerical stability.
**Backend fallback**: try candidate list; first `is_available()` returning True selected; else raise → handled at chat layer.

### Potential Improvements

- Stream artifact download directly from GridFS (async iterator) instead of buffering entire file.
- Switch FAISS index type to `IndexIVFFlat` for large transcripts (requires training).
- Introduce hierarchical summarization for ultra-long transcripts before RAG build (two-pass summarization).
- Move PDF generation to async subprocess or worker to avoid blocking event loop.
- Add structured error schema (e.g., `{code, message, details}`) across all endpoints.

## API Endpoints (Actual)

- GET `/api/v1/health` / `/api/v1/ready`
- POST `/api/v1/process`
- GET `/api/v1/reports` (pagination + filter)
- GET `/api/v1/reports/{id}`
- GET `/api/v1/reports/{id}/download?type=html|pdf`
- GET `/api/v1/videos/{video_id}/rag`
- GET `/api/v1/videos/{video_id}/transcript`
- GET `/api/v1/videos/{video_id}/chunks`
- POST `/api/v1/chat`
- GET `/api/v1/config`

### Planned Future Endpoints

- Tricks, sticky notes, manual transcript upload, conversation history, rate limit status.

## Data Model (Current + Future)

- `reports`: `{ _id, youtube_url, video_id?, title?, status, artifacts{html_file_id?, pdf_file_id?}, created_at, updated_at, error? }`
- (future) `conversations`: `{ user_id, video_id, messages[], created_at, updated_at, summary?, notes?, tricks?, sticky_notes?, mermaid_code? }`
- (future) `transcripts_cache`: `{ video_id, items[], cached_at }`
- (future) `pdfs`: superseded by artifacts in reports (GridFS metadata).

## Config & Environment

Required: `GOOGLE_API_KEY` / `GEMINI_API_KEY`  
Optional: `MONGODB_URI`, `MONGODB_DB`, `REDIS_URL` (if used)  
General: `APP_ENV`, `LOG_LEVEL`, `CORS_ALLOWED_ORIGINS`  
Feature Flags: `USE_RAG`  
LLM Tuning: `GEMINI_MODEL`, `TEMPERATURE`, `MAX_TOKENS`  
Rate Limiting: `RATE_LIMIT_CALLS`, `RATE_LIMIT_PERIOD`  
Proxy: `HTTPS_PROXY`, `HTTP_PROXY` (optional)

## Dependencies (No Paid Vendors)

**Backend**: fastapi, uvicorn, motor, pymongo, langchain, langchain-google-genai, langchain-community, youtube-transcript-api, pyppeteer/weasyprint, python-dotenv, pydantic, pydantic-settings, sentence-transformers, faiss-cpu, loguru.  
**Frontend**: react, typescript, vite, tailwindcss, @tanstack/react-query, mermaid.  
**Optional**: faiss-cpu (skip if unsupported).

## LLM Model Usage & Selection

**Chat / Generation:** `qwen2.5:7b` via Ollama (default in `OllamaBackend`). All interactive answers (chat endpoint and pipeline summary/notes/mindmap generators) currently resolve to Qwen unless Gemini is explicitly requested.

**Gemini:** Backend support exists (`GeminiBackend`) but is largely dormant due to rate limits and key constraints. Fallback logic tries Ollama first; Gemini is only invoked if Ollama is unavailable and a valid key is present.

**Embeddings (RAG):** `sentence-transformers/all-MiniLM-L6-v2` (see `rag_store.py`). Used solely for embeddings powering FAISS semantic similarity and timestamp-window retrieval; not for text generation.

**Pipeline Artifacts:** Summary, notes, and mind map modules import an LLM backend lazily; current configuration resolves to Qwen for generation steps.

### How Selection Works

- **Chat:** If `backend` is omitted in request payload, `auto_select_backend("ollama", model)` selects Ollama/Qwen if available; Gemini only if Ollama fails and a Gemini key is configured.
- **RAG Retrieval:** Independent of generation backend—embeddings always MiniLM.

### Future Adjustments (Planned)

- Config flag to force Gemini for high quality summaries while keeping chat on Qwen.
- Optional lighter local model variant for faster draft summaries.
- Caching layer for Gemini calls to mitigate rate limits.


## Error Handling & UX

- Distinguish transcript errors: Blocked / NotFound / Disabled (manual paste prompt).
- LLM: retry with backoff on 429/5xx.
- PDF: clear error if renderer missing with install hint.
- Consistent JSON error schema: `{ code, message }` (planned standardization).

## Rate Limiting & Caching (Planned)

- In-memory token bucket per IP/user.
- Transcript & LLM output caching (memory/JSON; Mongo if available).

## Testing

**Existing**: health, request logging.  
**Needed**: process lifecycle, pagination, artifact download, chat (RAG & non-RAG), transcript/chunks endpoints.  
**Future**: manual transcript fallback, memory aids, sticky notes, rate limiting.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| YouTube transcript blocked | Pipeline stalls | Manual paste fallback UI |
| FAISS build slow | Delayed RAG availability | Lazy build + progress (future) |
| Gemini rate limits | Slower responses | Retry + caching |
| Very large transcripts | Context overflow | Chunking + hierarchical summarization (future) |
| Artifact storage growth | Disk pressure | Retention/cleanup policy (future) |

## Milestones

- M1 (Done): Processing pipeline, reports CRUD, health/ready, config.
- M2 (In Progress): Chat + RAG, artifact download.
- M3 (Next): Memory aids, sticky notes, conversation persistence.
- M4: Rate limiting, structured logging, file-based storage adapter.
- M5: Docker Compose, CI pipeline, retention & cleanup, manual transcript upload.

## Acceptance Criteria

**MVP**: User submits YouTube URL → processing job succeeds → downloadable HTML/PDF includes summary, notes, mind map; chat answers with citations when RAG active; health shows Mongo status; config exposes flags.  
**Post-MVP**: Memory aids + sticky notes rendered; persistent conversation memory; manual transcript path for blocked fetches.  
**Cost**: No paid services beyond Gemini.  
**UX**: Clear error messages for transcript failure & missing artifacts.

## Deployment

- Local dev: uvicorn reload; optional Docker Compose (Mongo + API).
- Single-node free tier: FastAPI app + local Mongo or file-based JSON persistence.

## Completeness Check

All original TRD topics are represented: transcript acquisition, pipeline, learning outputs, chat/RAG, PDF export, persistence, security, observability, config/env, dependencies, error handling, caching/rate limiting, testing, risks, milestones, acceptance criteria, deployment. Added explicit current vs planned delineations.

---
TRD.md generated from `trd.txt` and aligned with current repository implementation plus planned extensions.
