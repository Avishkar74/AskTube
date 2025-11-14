#!/usr/bin/env python3
"""
AskTube CLI - YouTube Learning Assistant

Complete pipeline: YouTube URL → Transcript → Summary → Notes → Mind Map

Usage:
    python asktube.py <youtube_url> [options]
    python asktube.py --transcript transcript.txt [options]
"""
import argparse
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
import re

# Import our modules
from transcript_extractor import get_transcript, save_transcript, extract_video_id
from summary_generator import summarize_text
from detail_explanation_generator import generate_notes
from mindmap_generator import generate_mindmap
from cache_manager import CacheManager


class AskTube:
    """Main orchestrator for the AskTube pipeline."""

    def __init__(
        self,
        output_dir: str = "outputs",
        use_cache: bool = True,
        cache_ttl: int = 86400,
    ):
        """Initialize AskTube.

        Args:
            output_dir: Directory for output files
            use_cache: Whether to use caching
            cache_ttl: Cache time-to-live in seconds
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.use_cache = use_cache
        if use_cache:
            self.cache = CacheManager(cache_dir="cache", default_ttl=cache_ttl)
        else:
            self.cache = None

    def _get_cached(self, key: str, namespace: str) -> Optional[Any]:
        """Get value from cache if enabled."""
        if self.cache and self.use_cache:
            return self.cache.get(key, namespace=namespace)
        return None

    def _set_cached(self, key: str, value: Any, namespace: str) -> None:
        """Set value in cache if enabled."""
        if self.cache and self.use_cache:
            self.cache.set(key, value, namespace=namespace)

    def process_url(
        self,
        youtube_url: str,
        model: str = "gemini-2.0-flash-lite",
        skip_summary: bool = False,
        skip_notes: bool = False,
        skip_mindmap: bool = False,
    ) -> Dict[str, Any]:
        """Process a YouTube URL through the full pipeline.

        Args:
            youtube_url: YouTube video URL
            model: Gemini model to use
            skip_summary: Skip summary generation
            skip_notes: Skip detailed notes generation
            skip_mindmap: Skip mind map generation

        Returns:
            Dictionary with paths to all generated files
        """
        print(f"\n{'='*60}")
        print(f"AskTube - YouTube Learning Assistant")
        print(f"{'='*60}\n")

        # Extract video ID
        video_id = extract_video_id(youtube_url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {youtube_url}")

        print(f"Video ID: {video_id}")

        results = {"video_id": video_id, "url": youtube_url}

        # Step 1: Extract transcript
        print(f"\n[1/4] Extracting transcript...")
        transcript_cache_key = f"transcript_{video_id}"
        cached_transcript = self._get_cached(transcript_cache_key, "transcripts")

        if cached_transcript:
            print("[OK]Using cached transcript")
            transcript_text = cached_transcript["text"]
            transcript_data = cached_transcript["data"]
        else:
            # Get transcript and save it
            transcript_items = get_transcript(youtube_url)
            save_transcript(transcript_items, video_id, output_dir=str(self.output_dir))

            # Convert to plain text
            transcript_text = " ".join([item["text"] for item in transcript_items])
            transcript_data = {"items": transcript_items, "text": transcript_text}

            # Cache the transcript
            self._set_cached(
                transcript_cache_key,
                {"text": transcript_text, "data": transcript_data},
                "transcripts",
            )
            print(f"[OK]Transcript extracted: {len(transcript_text)} characters")

        results["transcript"] = {
            "json": str(self.output_dir / f"{video_id}.json"),
            "txt": str(self.output_dir / f"{video_id}.txt"),
            "timestamped": str(self.output_dir / f"{video_id}_timestamped.txt"),
        }

        # Step 2: Generate summary
        if not skip_summary:
            print(f"\n[2/4] Generating summary...")
            summary_cache_key = f"summary_{video_id}_{model}"
            cached_summary = self._get_cached(summary_cache_key, "outputs")

            if cached_summary:
                print("[OK]Using cached summary")
                summary = cached_summary
            else:
                summary = summarize_text(
                    transcript_text, model=model, per_chunk_chars=8000
                )
                self._set_cached(summary_cache_key, summary, "outputs")
                print(f"[OK]Summary generated")

            summary_path = self.output_dir / f"{video_id}_summary.txt"
            summary_path.write_text(summary, encoding="utf-8")
            results["summary"] = str(summary_path)
        else:
            print(f"\n[2/4] Skipping summary...")

        # Step 3: Generate detailed notes
        if not skip_notes:
            print(f"\n[3/4] Generating detailed notes...")
            notes_cache_key = f"notes_{video_id}_{model}"
            cached_notes = self._get_cached(notes_cache_key, "outputs")

            if cached_notes:
                print("[OK]Using cached notes")
                notes = cached_notes
            else:
                notes = generate_notes(
                    transcript_text, model=model, per_chunk_chars=8000
                )
                self._set_cached(notes_cache_key, notes, "outputs")
                print(f"[OK]Notes generated")

            notes_json_path = self.output_dir / f"{video_id}_notes.json"
            notes_md_path = self.output_dir / f"{video_id}_notes.md"

            notes_json_path.write_text(
                json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            # Generate markdown
            md_lines = ["# Study Notes", ""]
            md_lines.append("## Summary\n" + notes["summary"].strip())
            md_lines.append("## Detailed Notes\n" + notes["detailed_notes"].strip())
            md_lines.append("## Key Concepts\n" + notes["key_concepts"].strip())
            md_lines.append("## Examples\n" + notes["examples"].strip())
            md_lines.append("## Memory Tricks\n" + notes["memory_tricks"].strip())
            md_lines.append("## Common Mistakes\n" + notes["common_mistakes"].strip())
            md_lines.append("## Sticky Notes\n" + notes["sticky_notes"].strip())
            notes_md_path.write_text("\n\n".join(md_lines), encoding="utf-8")

            results["notes"] = {"json": str(notes_json_path), "md": str(notes_md_path)}
        else:
            print(f"\n[3/4] Skipping detailed notes...")

        # Step 4: Generate mind map
        if not skip_mindmap:
            print(f"\n[4/4] Generating mind map...")
            mindmap_cache_key = f"mindmap_{video_id}_{model}"
            cached_mindmap = self._get_cached(mindmap_cache_key, "outputs")

            if cached_mindmap:
                print("[OK]Using cached mind map")
                mindmap = cached_mindmap
            else:
                mindmap = generate_mindmap(
                    transcript_text, model=model, per_chunk_chars=8000
                )
                self._set_cached(mindmap_cache_key, mindmap, "outputs")
                print(f"[OK]Mind map generated")

            mindmap_path = self.output_dir / f"{video_id}_mindmap.mmd"
            mindmap_path.write_text(mindmap, encoding="utf-8")
            results["mindmap"] = str(mindmap_path)
        else:
            print(f"\n[4/4] Skipping mind map...")

        return results

    def process_transcript_file(
        self,
        transcript_path: str,
        output_prefix: str = "custom",
        model: str = "gemini-2.0-flash-lite",
        skip_summary: bool = False,
        skip_notes: bool = False,
        skip_mindmap: bool = False,
    ) -> Dict[str, Any]:
        """Process a transcript file through the pipeline (skip extraction).

        Args:
            transcript_path: Path to transcript text file
            output_prefix: Prefix for output files
            model: Gemini model to use
            skip_summary: Skip summary generation
            skip_notes: Skip detailed notes generation
            skip_mindmap: Skip mind map generation

        Returns:
            Dictionary with paths to all generated files
        """
        print(f"\n{'='*60}")
        print(f"AskTube - Processing Transcript File")
        print(f"{'='*60}\n")

        transcript_text = Path(transcript_path).read_text(encoding="utf-8")
        print(f"Loaded transcript: {len(transcript_text)} characters")

        results = {"source": transcript_path}

        # Generate summary
        if not skip_summary:
            print(f"\n[1/3] Generating summary...")
            summary = summarize_text(transcript_text, model=model, per_chunk_chars=8000)
            summary_path = self.output_dir / f"{output_prefix}_summary.txt"
            summary_path.write_text(summary, encoding="utf-8")
            results["summary"] = str(summary_path)
            print(f"[OK]Summary generated")
        else:
            print(f"\n[1/3] Skipping summary...")

        # Generate detailed notes
        if not skip_notes:
            print(f"\n[2/3] Generating detailed notes...")
            notes = generate_notes(transcript_text, model=model, per_chunk_chars=8000)

            notes_json_path = self.output_dir / f"{output_prefix}_notes.json"
            notes_md_path = self.output_dir / f"{output_prefix}_notes.md"

            notes_json_path.write_text(
                json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            md_lines = ["# Study Notes", ""]
            md_lines.append("## Summary\n" + notes["summary"].strip())
            md_lines.append("## Detailed Notes\n" + notes["detailed_notes"].strip())
            md_lines.append("## Key Concepts\n" + notes["key_concepts"].strip())
            md_lines.append("## Examples\n" + notes["examples"].strip())
            md_lines.append("## Memory Tricks\n" + notes["memory_tricks"].strip())
            md_lines.append("## Common Mistakes\n" + notes["common_mistakes"].strip())
            md_lines.append("## Sticky Notes\n" + notes["sticky_notes"].strip())
            notes_md_path.write_text("\n\n".join(md_lines), encoding="utf-8")

            results["notes"] = {"json": str(notes_json_path), "md": str(notes_md_path)}
            print(f"[OK]Notes generated")
        else:
            print(f"\n[2/3] Skipping detailed notes...")

        # Generate mind map
        if not skip_mindmap:
            print(f"\n[3/3] Generating mind map...")
            mindmap = generate_mindmap(transcript_text, model=model, per_chunk_chars=8000)
            mindmap_path = self.output_dir / f"{output_prefix}_mindmap.mmd"
            mindmap_path.write_text(mindmap, encoding="utf-8")
            results["mindmap"] = str(mindmap_path)
            print(f"[OK]Mind map generated")
        else:
            print(f"\n[3/3] Skipping mind map...")

        return results


def main():
    parser = argparse.ArgumentParser(
        description="AskTube - YouTube Learning Assistant CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a YouTube URL
  python asktube.py "https://www.youtube.com/watch?v=VIDEO_ID"

  # Process a transcript file
  python asktube.py --transcript transcript.txt

  # Disable caching
  python asktube.py URL --no-cache

  # Skip certain outputs
  python asktube.py URL --skip-mindmap --skip-summary
        """,
    )

    parser.add_argument(
        "url", nargs="?", help="YouTube URL to process (if not using --transcript)"
    )
    parser.add_argument(
        "--transcript", "-t", help="Process a transcript file instead of YouTube URL"
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="outputs",
        help="Output directory (default: outputs)",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="gemini-2.0-flash-lite",
        help="Gemini model (default: gemini-2.0-flash-lite)",
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Disable caching"
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=86400,
        help="Cache TTL in seconds (default: 86400 = 24h)",
    )
    parser.add_argument(
        "--skip-summary", action="store_true", help="Skip summary generation"
    )
    parser.add_argument(
        "--skip-notes", action="store_true", help="Skip detailed notes generation"
    )
    parser.add_argument(
        "--skip-mindmap", action="store_true", help="Skip mind map generation"
    )
    parser.add_argument(
        "--output-prefix",
        default="custom",
        help="Output filename prefix for transcript files (default: custom)",
    )

    args = parser.parse_args()

    # Validate input
    if not args.url and not args.transcript:
        parser.error("Either provide a YouTube URL or use --transcript with a file path")

    if args.url and args.transcript:
        parser.error("Cannot specify both URL and --transcript")

    try:
        # Initialize AskTube
        asktube = AskTube(
            output_dir=args.output_dir,
            use_cache=not args.no_cache,
            cache_ttl=args.cache_ttl,
        )

        # Process input
        if args.transcript:
            results = asktube.process_transcript_file(
                transcript_path=args.transcript,
                output_prefix=args.output_prefix,
                model=args.model,
                skip_summary=args.skip_summary,
                skip_notes=args.skip_notes,
                skip_mindmap=args.skip_mindmap,
            )
        else:
            results = asktube.process_url(
                youtube_url=args.url,
                model=args.model,
                skip_summary=args.skip_summary,
                skip_notes=args.skip_notes,
                skip_mindmap=args.skip_mindmap,
            )

        # Print results
        print(f"\n{'='*60}")
        print(f"Processing Complete!")
        print(f"{'='*60}\n")
        print("Generated files:")
        for key, value in results.items():
            if key in ["video_id", "url", "source"]:
                continue
            if isinstance(value, dict):
                print(f"\n{key.upper()}:")
                for subkey, subvalue in value.items():
                    print(f"  -{subkey}: {subvalue}")
            else:
                print(f"  -{key}: {value}")

        return 0

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
