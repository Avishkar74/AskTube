import youtube_transcript_api
import sys

with open('path.txt', 'w') as f:
    f.write(f"File: {getattr(youtube_transcript_api, '__file__', 'unknown')}\n")
    f.write(f"Version: {getattr(youtube_transcript_api, '__version__', 'unknown')}\n")
    f.write(f"Path: {getattr(youtube_transcript_api, '__path__', 'unknown')}\n")

