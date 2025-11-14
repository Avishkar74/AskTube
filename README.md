# AskTube - YouTube Learning Assistant

Transform YouTube videos into comprehensive study materials using AI.

AskTube extracts transcripts from YouTube videos and generates multiple learning artifacts including summaries, detailed notes, mind maps, and more - all powered by Google's Gemini API.

## Features

- **Transcript Extraction**: Automatically fetch transcripts from YouTube videos
- **Smart Summarization**: Generate concise summaries with key points
- **Detailed Study Notes**: Structured notes with:
  - Summary and overview
  - Detailed explanations
  - Key concepts and definitions
  - Examples and use cases
  - Memory tricks and mnemonics
  - Common mistakes to avoid
  - Quick revision sticky notes
- **Mind Maps**: Visual learning with Mermaid mindmap syntax
- **Intelligent Caching**: Avoid redundant API calls with built-in caching
- **Multiple Output Formats**: JSON, Markdown, and Mermaid
- **CLI Interface**: Easy-to-use command-line tool

## Installation

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd asktube
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API key:

Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
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
```

### View All Options

```bash
python asktube.py --help
```

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
├── transcript_extractor.py         # YouTube transcript extraction
├── summary_generator.py            # Summary generation
├── detail_explanation_generator.py # Detailed notes generation
├── mindmap_generator.py            # Mind map generation
├── cache_manager.py                # Caching system
├── outputs/                        # Generated files
├── cache/                          # Cache storage
│   ├── transcripts/               # Cached transcripts
│   └── outputs/                   # Cached generated content
├── .env                           # API keys (create this)
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## How It Works

1. **Transcript Extraction**: Fetches the video transcript using `youtube-transcript-api`
2. **Intelligent Chunking**: Long transcripts are split into manageable chunks
3. **AI Processing**: Each chunk is processed by Google Gemini with specialized prompts
4. **Output Generation**: Results are formatted into multiple learning artifacts
5. **Caching**: All outputs are cached to save API calls and processing time

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

## Milestones

- [x] **M1**: Transcript + Summary + Notes
- [x] **M2**: Mind map + Caching + CLI Orchestrator
- [ ] **M3**: Chat with memory + PDF export
- [ ] **M4**: Optional FAISS RAG + Observability
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
