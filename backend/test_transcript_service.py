import sys
import os

# Add the backend directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.transcript_service import get_transcript_segments
from app.core.logging import logger

# Configure logger to print to console
logger.add(sys.stderr, level="INFO")

def test_fetch():
    video_url = "https://youtu.be/IFkDbsgn8yg" # The video that was failing
    print(f"Testing transcript fetch for: {video_url}")
    
    try:
        segments = get_transcript_segments(video_url)
        print(f"SUCCESS: Fetched {len(segments)} segments")
        print(f"Sample: {segments[:1]}")
    except Exception as e:
        print(f"FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fetch()
