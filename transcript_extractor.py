"""YouTube Transcript Extractor - Standalone (No LangChain)

Direct implementation using youtube-transcript-api only.
Avoids all LangChain dependency conflicts.
"""

from youtube_transcript_api import YouTubeTranscriptApi
import re
import json
from pathlib import Path
from typing import List, Dict, Optional
try:
    from pytube import YouTube
    PYTUBE_AVAILABLE = True
except ImportError:
    PYTUBE_AVAILABLE = False


def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:shorts\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from: {url}")


def get_video_title(video_url: str) -> Optional[str]:
    """Extract video title from YouTube URL.

    Args:
        video_url: YouTube video URL or video ID

    Returns:
        Video title if successful, None if pytube not available or extraction fails
    """
    if not PYTUBE_AVAILABLE:
        print("[INFO] pytube not installed. Install with: pip install pytube")
        return None

    try:
        # Ensure we have a full URL
        video_id = extract_video_id(video_url)
        full_url = f"https://youtube.com/watch?v={video_id}"

        yt = YouTube(full_url)
        title = yt.title
        print(f"[VIDEO] Title: {title}")
        return title

    except Exception as e:
        print(f"[WARNING] Could not extract video title: {e}")
        return None


def get_transcript(video_url: str, language: str = 'en') -> List[Dict]:
    """Fetch transcript for a YouTube video.
    
    Args:
        video_url: YouTube video URL
        language: Preferred language code (default: 'en')
        
    Returns:
        List of transcript segments with 'text', 'start', 'duration'
    """
    video_id = extract_video_id(video_url)
    print(f"[VIDEO] Video ID: {video_id}")
    print(f"[INFO] Fetching transcript...")

    try:
        # Use the .fetch() method and convert to list
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=[language])

        # Convert FetchedTranscript to list of plain dicts
        transcript = [{'text': item.text, 'start': item.start, 'duration': item.duration}
                      for item in fetched]

        print(f"[OK] Found transcript ({len(transcript)} segments)")
        return transcript

    except Exception as e:
        print(f"[WARNING] Error: {e}")

        # List available transcripts using .list() method
        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            print("\n[INFO] Available transcripts:")
            for t in transcript_list:
                print(f"   - {t}")

            # Try to fetch first available
            print("\n[INFO] Attempting to fetch first available transcript...")
            fetched = api.fetch(video_id)
            transcript = [{'text': item.text, 'start': item.start, 'duration': item.duration}
                          for item in fetched]

            print(f"[OK] Got transcript ({len(transcript)} segments)")
            return transcript

        except Exception as list_error:
            print(f"[ERROR] Could not list transcripts: {list_error}")
            raise


def save_transcript(transcript: List[Dict], video_id: str, output_dir: str = "outputs"):
    """Save transcript as JSON and plain text files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save JSON (structured data)
    json_file = output_path / f"{video_id}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)
    
    # Save TXT (plain text)
    txt_file = output_path / f"{video_id}.txt"
    full_text = " ".join([entry['text'] for entry in transcript])
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(full_text)
    
    # Save timestamped version
    timestamped_file = output_path / f"{video_id}_timestamped.txt"
    with open(timestamped_file, "w", encoding="utf-8") as f:
        for entry in transcript:
            timestamp = f"[{entry['start']:.2f}s]"
            f.write(f"{timestamp} {entry['text']}\n")
    
    print(f"\n[SAVED] Files created:")
    print(f"   - {json_file.name} - {len(transcript)} segments")
    print(f"   - {txt_file.name} - {len(full_text):,} characters")
    print(f"   - {timestamped_file.name} - with timestamps")
    print(f"\n[OUTPUT] Directory: {output_path.absolute()}")


def main():
    """Main execution."""
    # Configuration
    video_url = "https://youtu.be/7nonQ2dYgiE?si=HbY7QL052sTngMSF"
    output_dir = "outputs/SpringBoot"
    
    print("=" * 60)
    print("YouTube Transcript Extractor")
    print("=" * 60)
    
    try:
        # Fetch transcript
        transcript = get_transcript(video_url)
        video_id = extract_video_id(video_url)
        
        # Save files
        save_transcript(transcript, video_id, output_dir)
        
        # Print sample
        print("\n" + "=" * 60)
        print("[SAMPLE] First 3 segments:")
        print("=" * 60)
        for entry in transcript[:3]:
            print(f"[{entry['start']:>7.2f}s] {entry['text']}")

        print("\n[OK] Success!")

    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())