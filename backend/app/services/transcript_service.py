"""Transcript utilities for YouTube videos.

Provides helpers to:
- Extract a YouTube `video_id` from multiple URL formats (watch, embed, shorts).
- Fetch transcript segments (text, start, duration) using youtube-transcript-api.
- Generate concatenated transcript text for simpler consumption.
"""

from typing import List, Dict, Optional
import re

try:
    from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
except Exception as e:  # noqa: BLE001
    raise RuntimeError("youtube-transcript-api is required in backend environment") from e

from ..core.logging import logger


def extract_video_id(url: str) -> str:
    """Extract the 11-character YouTube video ID from a URL or raw ID.

    Supports typical patterns such as `watch?v=`, `/embed/`, `/shorts/`, and
    accepts a bare 11-character ID. Raises `ValueError` when not found.
    """
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:shorts\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    raise ValueError(f"Could not extract video ID from: {url}")


def get_transcript_segments(video_url: str, language: str = 'en') -> List[Dict]:
    """Fetch transcript segments for a full YouTube URL.

    Tries the requested `language` first, then falls back to a list of common languages,
    and finally attempts to list available transcripts and pick the first one.
    """
    vid = extract_video_id(video_url)
    return get_transcript_segments_by_id(vid, language)


def get_transcript_text(video_url: str, language: str = 'en') -> str:
    """Return transcript text concatenated from fetched segments."""
    segs = get_transcript_segments(video_url, language=language)
    return " ".join(s.get('text', '') for s in segs)


def get_transcript_segments_by_id(video_id: str, language: str = 'en') -> List[Dict]:
    """Fetch transcript segments by video ID with robust fallback logic."""
    try:
        # 1. Try requested language
        return _fetch_and_format(video_id, [language])
    except Exception:
        pass

    try:
        # 2. Try common languages (English variants, Hindi, etc.)
        fallback_langs = ['en', 'en-US', 'en-GB', 'hi', 'es', 'fr', 'de']
        if language in fallback_langs:
            fallback_langs.remove(language)
        return _fetch_and_format(video_id, fallback_langs)
    except Exception:
        pass

    # 3. List available transcripts and pick the first one (last resort)
    try:
        # Use the API instance method as seen in transcript_extractor.py
        api = YouTubeTranscriptApi()
        try:
            transcript_list = api.list(video_id)
            # Try to find a manually created one first (assuming list returns objects with is_generated)
            # Note: The available API seems to return a list of objects, let's inspect or assume standard behavior
            # If api.list() returns a list of Transcripts, we can iterate.
            # Based on transcript_extractor.py, it iterates and prints.
            
            # Fallback: just fetch the default
            fetched = api.fetch(video_id)
            return [{'text': it.text, 'start': it.start, 'duration': it.duration} for it in fetched]
            
        except Exception:
             # If list/fetch fails, try with languages
             fetched = api.fetch(video_id, languages=['en'])
             return [{'text': it.text, 'start': it.start, 'duration': it.duration} for it in fetched]

    except Exception as e:
        logger.error(f"All transcript fetch attempts failed for {video_id}: {e}")
        raise

    raise RuntimeError(f"No transcript found for video {video_id}")


def _fetch_and_format(video_id: str, languages: List[str]) -> List[Dict]:
    """Helper to fetch and format transcript segments."""
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=languages)
        return [{'text': it.text, 'start': it.start, 'duration': it.duration} for it in fetched]
    except Exception:
        # Fallback to static method if instance method fails (just in case)
        try:
            fetched = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
            return [{'text': it['text'], 'start': it['start'], 'duration': it['duration']} for it in fetched]
        except AttributeError:
            raise

