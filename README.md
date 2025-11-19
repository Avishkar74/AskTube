# AskTube - YouTube Learning Assistant

Transform YouTube videos into comprehensive study materials using AI.

AskTube extracts transcripts from YouTube videos and generates multiple learning artifacts including summaries, detailed notes, mind maps, and PDFs. It supports both local and cloud LLM backends (Ollama and Gemini), optional RAG with FAISS, and a FastAPI backend for programmatic access.

## Features

- **Transcript Extraction**: Automatically fetch transcripts from YouTube videos
- **Smart Summarization**: Generate concise summaries with key points
- **Detailed Study Notes**: Structured notes (summary, explanations, concepts, examples, memory tricks, mistakes, sticky notes)
- **Mind Maps**: Visual learning with Mermaid mindmap syntax
- **PDF/HTML Export**: Beautiful, styled exports (falls back to HTML if `weasyprint` is not installed)
- **RAG (Optional)**: FAISS + sentence-transformers retrieval with chunk metadata and citations
- **Local/Cloud LLM Backends**: Use Ollama (e.g., `qwen2.5:7b`) or Gemini (`gemini-2.0-flash-lite`)
- **FastAPI Backend**: Versioned API under `/api/v1` with health/ready, processing, reports, transcript/chunks, and chat endpoints
- **Request Tracing**: Request ID propagation (`X-Request-ID`) and latency logging middleware
- **Intelligent Caching**: Avoid redundant work with built-in TTL cache
- **Multiple Output Formats**: JSON, Markdown, Mermaid, and PDF/HTML
- **CLI + Chat CLI**: End-to-end processing and interactive Q&A from the terminal

## Installation

### Prerequisites

- Python 3.8 or higher
- For Gemini: a Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Optional for local LLM: [Ollama](https://ollama.com) installed and a pulled model (e.g., `ollama pull qwen2.5:7b`)
- Optional for backend: a MongoDB instance (local or Atlas) if you plan to run the FastAPI server

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd asktube
```

2. (Recommended) Create a virtual environment and install dependencies:
```bash
python -m venv .venv
. .venv/Scripts/Activate.ps1  # PowerShell on Windows
pip install -r requirements.txt
```

3. Set up environment variables:

Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
# Optional (backend):
# MONGODB_URI=mongodb://localhost:27017
# MONGODB_DB_NAME=asktube
# USE_RAG=true
```

Or export as environment variable:
```bash
export GOOGLE_API_KEY=your_gemini_api_key_here
```

## Usage

### Process a YouTube Video

```bash
python asktube.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Process a Transcript File

```bash
python asktube.py --transcript transcript.txt
```

### Advanced Options

```bash
# Disable caching
python asktube.py URL --no-cache

# Skip specific outputs
python asktube.py URL --skip-summary --skip-mindmap

# Custom output directory and prefix
python asktube.py --transcript file.txt --output-dir my_outputs --output-prefix lesson1

# Use different Gemini model
python asktube.py URL --model gemini-pro

# Set custom cache TTL (in seconds)
python asktube.py URL --cache-ttl 3600

# Select backend and model
python asktube.py URL -b ollama -m qwen2.5:7b
python asktube.py URL -b gemini -m gemini-2.0-flash-lite

# Generate a polished PDF (or HTML fallback if PDF engine missing)
python asktube.py URL --generate-pdf

# Force FAISS re-index (when RAG is enabled)
python asktube.py URL --force-reindex
```

### View All Options

```bash
python asktube.py --help
```

### Chat About a Video (Chat CLI)

Interactive Q&A about a YouTube video with optional RAG and backend selection:

```bash
python chat_cli.py "https://www.youtube.com/watch?v=VIDEO_ID" \
	--user-id alice -b ollama -m qwen2.5:7b --use-rag

# Or chat from a transcript file
python chat_cli.py --transcript transcript.txt --video-id my_video --use-rag
```

Flags:
- `--backend/-b`: `ollama` (default) or `gemini`
- `--model/-m`: model name (defaults as above)
- `--use-rag/--no-rag`: toggle retrieval
- `--force-reindex`: rebuild FAISS index for the transcript before chat

## Output Files

AskTube generates the following files in the `outputs/` directory:

| File | Description |
|------|-------------|
| `{video_id}.json` | Raw transcript with timestamps (JSON) |
| `{video_id}.txt` | Plain text transcript |
| `{video_id}_timestamped.txt` | Transcript with timestamps |
| `{video_id}_summary.txt` | Concise summary with key points |
| `{video_id}_notes.json` | Structured study notes (JSON) |
| `{video_id}_notes.md` | Formatted study notes (Markdown) |
| `{video_id}_mindmap.mmd` | Mind map in Mermaid syntax |
| `pdfs/{title_or_prefix}_YYYYMMDD_HHMMSS.pdf` | Styled PDF export (falls back to `.html` if PDF engine unavailable) |

## Examples

### Example 1: Learn from a Tutorial

```bash
python asktube.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Output:
- Summary of main concepts
- Detailed notes organized by topic
- Mind map showing relationships
- All cached for instant re-access

### Example 2: Process Multiple Videos

```bash
# Process first video
python asktube.py "https://youtube.com/watch?v=video1"

# Process second video (cached independently)
python asktube.py "https://youtube.com/watch?v=video2"
```

### Example 3: Manual Transcript Input

If YouTube blocks transcript fetching, you can manually paste the transcript:

```bash
# Save transcript to file
echo "Your transcript here..." > my_transcript.txt

# Process it
python asktube.py --transcript my_transcript.txt --output-prefix my_lesson
```

## Project Structure

```
asktube/
├── asktube.py                      # Main CLI orchestrator
├── chat_cli.py                     # Interactive chat about a video
├── conversation_manager.py         # Chat memory + RAG prompt builder
├── transcript_extractor.py         # YouTube transcript extraction
├── summary_generator.py            # Summary generation
├── detail_explanation_generator.py # Detailed notes generation
├── mindmap_generator.py            # Mind map generation
├── cache_manager.py                # Caching system
├── llm_backend.py                  # Ollama/Gemini abstraction
├── rag_chunker.py                  # Split transcript into chunks
├── rag_embeddings.py               # SentenceTransformers embeddings
├── rag_faiss_store.py              # FAISS store + metadata
├── rag_indexer.py                  # One-shot indexing for a transcript
├── outputs/                        # Generated files
├── cache/                          # Cache storage
│   ├── transcripts/               # Cached transcripts
│   └── outputs/                   # Cached generated content
├── .env                           # API keys (create this)
├── requirements.txt               # Python dependencies
├── backend/                        # FastAPI service (Mongo, GridFS, RAG, chat)
│   ├── app/
│   │   ├── main.py                # App factory; CORS, middleware, routers
│   │   ├── api/v1/...             # Health, reports, chat routes
│   │   ├── services/...           # Processing, RAG, chat orchestration
│   │   ├── db/...                 # Motor + GridFS init/helpers
│   │   └── middleware/...         # Request ID + latency logging
│   └── tests/                     # Smoke tests (httpx ASGITransport)
└── README.md                      # This file
```

## How It Works

1. **Transcript Extraction**: Fetches the video transcript using `youtube-transcript-api`
2. **Intelligent Chunking**: Long transcripts are split into manageable chunks
3. **AI Processing**: Each chunk is processed by Google Gemini with specialized prompts
4. **Output Generation**: Results are formatted into multiple learning artifacts
5. **Caching**: All outputs are cached to save API calls and processing time

### Retrieval-Augmented Generation (RAG)

- Embeddings via `sentence-transformers/all-MiniLM-L6-v2`
- Vector store via FAISS with per-chunk metadata (video_id, chunk_id, token_estimate, transcript hash)
- Index is built on-demand (`rag_indexer.index_transcript`) and used by Chat CLI when `USE_RAG=true` or `--use-rag`

## API Rate Limiting

AskTube handles Gemini API rate limits automatically with:
- Exponential backoff (2s, 4s, 8s, 16s, 32s, 64s)
- Jitter to prevent thundering herd
- Up to 6 retry attempts
- Clear progress indicators

## Caching System

### Cache Organization

- **Transcripts**: 7-day TTL (rarely change)
- **Generated Outputs**: 24-hour TTL (can regenerate with different prompts)

### Cache Management

```bash
# Clear expired caches
python -c "from cache_manager import CacheManager; cm = CacheManager(); print(f'Cleared {cm.clear_expired()} expired caches')"

# View cache stats
python -c "from cache_manager import CacheManager; cm = CacheManager(); print(cm.get_stats())"
```

## Mind Map Visualization

The generated `.mmd` files use Mermaid syntax and can be visualized using:

- [Mermaid Live Editor](https://mermaid.live/)
- VS Code with Mermaid extension
- GitHub (renders automatically in markdown)
- [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) for PNG/SVG export

## Troubleshooting

### Transcript Not Available

**Problem**: YouTube video has no captions or they're disabled.

**Solution**: Manually provide transcript using `--transcript` flag.

### API Rate Limit Errors

**Problem**: Getting 429 errors from Gemini API.

**Solution**: The tool handles this automatically with retries. If persistent, wait a few minutes or use caching with `--no-cache` disabled.

### JSON Parsing Errors

**Problem**: LLM output is malformed JSON.

**Solution**: The tool has multiple fallback strategies. If errors persist, try a different Gemini model with `--model`.

### Unicode/Encoding Errors on Windows

**Problem**: Console display errors with special characters.

**Solution**: The tool has been updated to avoid Unicode characters. Ensure your console encoding is set correctly:
```bash
chcp 65001
```

## Development

### Module Overview

- **transcript_extractor.py**: Handles YouTube API interactions and transcript fetching
- **summary_generator.py**: Creates concise summaries using LangChain + Gemini
- **detail_explanation_generator.py**: Generates comprehensive study notes with 7 sections
- **mindmap_generator.py**: Creates hierarchical mind maps in Mermaid format
- **cache_manager.py**: File-based caching with TTL and namespace support
- **asktube.py**: Orchestrates the entire pipeline with CLI interface

### Running Individual Modules

Each module can be run independently:

```bash
# Extract transcript only
python transcript_extractor.py "https://youtube.com/watch?v=..."

# Generate summary only
python summary_generator.py --input transcript.txt --output summary.txt

# Generate detailed notes
python detail_explanation_generator.py --input transcript.txt

# Generate mind map
python mindmap_generator.py --input transcript.txt --output mindmap.mmd
```

## FastAPI Backend

Run the API server (PowerShell, from repo root):

```powershell
# Ensure env is active and backend env vars are set in backend/.env
& .\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

Key endpoints (prefix `API_PREFIX` = `/api`):
- `GET /api/v1/health`: service liveness
- `GET /api/v1/ready`: readiness incl. Mongo
- `POST /api/v1/process`: start processing (URL or transcript) and persist artifacts
- `GET /api/v1/reports`: list reports with pagination (`limit`, `offset`) and `total`
- `GET /api/v1/reports/{id}` / `download?format=html|pdf`: fetch report or artifact
- `GET /api/v1/videos/{video_id}/transcript`: segments for a video
- `GET /api/v1/videos/{video_id}/chunks`: RAG chunks metadata
- `GET /api/v1/videos/{video_id}/rag`: RAG status/stats
- `POST /api/v1/chat`: chat with optional `top_k`, `timestamp` + `window_s`, structured citations

Headers:
- `X-Request-ID`: sent/propagated per request; server logs include method, path, status, duration_ms

Backend environment (`backend/.env`):
- `MONGODB_URI=mongodb://localhost:27017` (or Atlas connection string)
- `MONGODB_DB_NAME=asktube`
- `ALLOWED_ORIGINS=http://localhost:5173` (adjust for your frontend)
- `USE_RAG=true|false`

## Milestones

- [x] **M1**: Transcript + Summary + Notes
- [x] **M2**: Mind map + Caching + CLI Orchestrator
- [x] **M3**: Chat with memory (Chat CLI) + PDF/HTML export
- [x] **M4**: FAISS RAG + Request tracing middleware (observability)
- [ ] **M5**: Full-stack web application (FastAPI + React)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

[Your License Here]

## Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) - LLM orchestration
- [Google Gemini](https://deepmind.google/technologies/gemini/) - AI model
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) - Transcript extraction
- [Mermaid](https://mermaid.js.org/) - Mind map visualization

## Support

For questions or issues, please open an issue on GitHub or contact [your-email].

---

**Made with Claude Code** 🤖

Now improved with a FastAPI backend, RAG, and Chat CLI.
