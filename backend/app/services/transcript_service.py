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

    Tries the requested `language` first, then falls back to the API's default
    selection. Returns a list of dicts: `{text, start, duration}`.
    """
    vid = extract_video_id(video_url)
    api = YouTubeTranscriptApi()
    try:
        fetched = api.fetch(vid, languages=[language])
    except Exception:
        # fallback to default selection
        fetched = api.fetch(vid)
    return [{'text': it.text, 'start': it.start, 'duration': it.duration} for it in fetched]


def get_transcript_text(video_url: str, language: str = 'en') -> str:
    """Return transcript text concatenated from fetched segments."""
    segs = get_transcript_segments(video_url, language=language)
    return " ".join(s.get('text', '') for s in segs)


def get_transcript_segments_by_id(video_id: str, language: str = 'en') -> List[Dict]:
    """Fetch transcript segments by video ID, mirroring `get_transcript_segments`."""
    api = YouTubeTranscriptApi()
    try:
        fetched = api.fetch(video_id, languages=[language])
    except Exception:
        fetched = api.fetch(video_id)
    return [{'text': it.text, 'start': it.start, 'duration': it.duration} for it in fetched]
