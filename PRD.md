# Product Requirements Document (PRD)

## 1. Product Vision

Transform any educational YouTube video into structured, high‑quality learning materials and an interactive Q&A experience—entirely with free/local components plus a single paid LLM (Gemini). The product minimizes friction (paste or auto-fetch transcript), maximizes retention (multi‑format outputs + spaced recall aids), and enables deep exploration (chat + optional RAG) while remaining cost‑conscious and deployable on a single developer machine or free VM.

## 2. Target Users & Personas

| Persona | Description | Primary Goals |
|---------|-------------|---------------|
| Self‑Learner | Individual upskilling via MOOCs / tutorials | Fast digestion, memory aids, revisit notes |
| Bootcamp Student | Structured study; needs consolidated material | Central PDF, mindmap, sticky notes |
| Instructor/TA | Curates supplemental study packs | Exportable, consistent formatting |
| Content Curator | Builds internal knowledge base from public videos | Batch processing + status tracking |

## 3. Value Propositions

1. End‑to‑end artifact generation in one click (summary → notes → mind map → PDF).
2. Resilient transcript acquisition (auto + manual fallback).
3. Cost discipline: no paid vector DBs, hosting, or observability vendors.
4. Deep Q&A with optional semantic/timestamp retrieval (RAG) when available.
5. Portable deployment (Docker Compose or local Python) and simple persistence (Mongo or JSON files).

## 4. Scope (MVP vs. Iterations)

### In Scope (MVP)

- Submit YouTube URL, process pipeline (transcript → summary → notes → mindmap → HTML/PDF).
- Download artifacts (HTML/PDF).
- Basic chat about video (transcript grounded; optional RAG if index exists).
- Status tracking via reports list + detail.
- Health & readiness endpoints.

### Deferred (Post‑MVP)

- Memory aids (mnemonics/analogies/acronyms).
- Sticky notes bullets.
- Persistent conversation memory by userId + videoId.
- Rate limiting & advanced caching tier.
- Frontend mind map rendering (Mermaid preview + PNG export).
- File‑based persistence abstraction fallback fully implemented.
- Docker & CI automation.

### Out of Scope

- Mobile apps, browser extensions.
- Additional paid APIs/services beyond Gemini.
- Hosted observability platforms; paid vector stores.

## 5. Feature Requirements (Detailed)

### 5.1 Video Processing Pipeline

Input: `youtube_url`  
Flow: Extract `video_id` → fetch transcript (auto) → generate summary, notes, mindmap → export combined HTML/PDF → upload artifact → persist report status/artifacts → optional FAISS index build.  
Non‑functional: Must start background task quickly (<200ms response); end‑to‑end typical completion <60s (LLM + export) for 1h video transcript (dependent on Gemini/CPU).  

### 5.2 Reports Management

Create job (queued → running → succeeded|failed).  
List with pagination + optional video filter.  
Retrieve single report (status, timestamps, artifact IDs).  
Download artifact (HTML or PDF).  

### 5.3 Chat & Retrieval

Input: `video_id` or `youtube_url`, `message`, optional `use_rag`, `top_k`, `window`.  
Behavior: If RAG enabled & index exists, semantic or timestamp-window retrieval; answer includes structured citations with chunk indices/start/end seconds. Fallback uses truncated transcript.  
Error Conditions: Missing video reference; backend unavailability; transcript unavailable (clear message).  

### 5.4 RAG Index

Construction: Segment-aware chunking preserving start/end; embedding with `all-MiniLM-L6-v2`; FAISS IP index stored locally + metadata JSON.  
Status: Endpoint returns `has_index`, `chunk_count`.  
Retrieval: Semantic top‑k and timestamp-based window.  

### 5.5 Configuration Discovery

Expose non-sensitive runtime flags: API prefix, RAG default, CORS origins, exposed headers, version.  

### 5.6 Health & Readiness

`/health` returns status (ok|degraded), timestamp, Mongo connectivity flag.  
`/ready` ensures DB availability with lightweight collection list.  

### 5.7 PDF/HTML Artifact

Single document combining summary, notes, mindmap, transcript (raw or truncated). Future: memory aids, sticky notes.  
Rendered via current HTML + (optional) WeasyPrint/pyppeteer; fallback HTML always stored.  

## 6. User Stories (MVP)

1. As a learner, I submit a YouTube URL and receive a structured PDF summarizing key points.  
2. As a learner, I ask clarifying questions about a processed video and get answers citing transcript chunks.  
3. As a curator, I monitor processing jobs with statuses and retry failed ones manually (future).  
4. As a frontend user, I can detect whether RAG is active to show retrieval toggles.  

## 7. Success Metrics

- Time‑to‑first‑artifact: < 60s for standard educational video (assuming transcript available).  
- Q&A citation usage rate: >70% of RAG answers show ≥1 citation.  
- Error fallbacks: 100% of transcript failures yield actionable manual paste message.  
- Artifact download success rate: >99% (HTML).  

## 8. KPIs & Analytics (Phase 2)

- Jobs processed per day.  
- Average chunk_count per video.  
- Chat sessions per video.  
- RAG usage ratio (RAG vs non‑RAG chats).  

## 9. Non‑Functional Requirements

- Performance: p95 API non‑LLM endpoints < 250ms; LLM endpoints dominated by Gemini latency.  
- Reliability: Graceful fallback path when transcript auto-fetch fails.  
- Cost: Only Gemini; no other paid dependencies.  
- Maintainability: Each service isolated (processing, rag_store, chat_service, gridfs).  

## 10. Assumptions

- Gemini key supplied at deploy time via .env or environment variables.  
- Local file system sufficient for FAISS + artifacts (<500MB typical).  
- Transcript length manageable within embedding + summarization limits (chunked).  

## 11. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| YouTube transcript blocked | Pipeline stalls | Manual paste fallback (future UI path) |
| FAISS build slow on low-end hardware | Delayed RAG readiness | Lazy index build + progress status (future) |
| Gemini rate limits | Delayed responses | Retry + local caching of outputs |
| Large transcripts exceed model context | Truncated answers | Chunk summarization + hierarchical summarization (future) |
| Storage bloat of artifacts | Disk pressure | Retention policy / periodic cleanup (future) |

## 12. Release Plan

Milestone mapping to TRD:

- M1: Processing pipeline + reports + health.  
- M2: Chat + basic RAG + config endpoint.  
- M3: PDF export stabilization + citations improvements.  
- M4: Memory aids, sticky notes, conversation persistence.  
- M5: Rate limiting, structured logs, Docker/CI.  

## 13. Open Questions

1. Will conversation memory require summarization or full log retention?  
2. Preferred PDF rendering engine final choice (WeasyPrint vs pyppeteer)?  
3. Should artifacts include rendered mind map PNG immediately or retain Mermaid source only?  
4. How to gracefully re‑queue failed processing jobs (manual or automatic)?  
5. Minimum retention period for artifacts & indexes?  

## 14. Acceptance Criteria (MVP)

- Given a valid YouTube URL with accessible transcript, user can trigger processing and later download HTML/PDF with summary/notes/mindmap.  
- Chat endpoint returns answers with citation objects when RAG is active.  
- Health and readiness endpoints reflect Mongo connectivity accurately.  
- Config endpoint returns stable prefix and flags for frontend adaptation.  

## 15. Future Enhancements (Post‑MVP)

- Conversation memory summarization to mitigate prompt growth.  
- Batch processing queue view + retries.  
- Visual timeline navigation (jump to transcript chunk timestamps).  
- Rate limiting (token bucket) + metrics dashboard (prometheus or simple counters).  
- Frontend “Manual Transcript Paste” flow.  

---
This PRD is synchronized with the current implemented backend (reports, processing, chat, RAG, config) and defers unimplemented TRD components into Post‑MVP sections.
