"""Playlist service for extracting YouTube playlist metadata using yt-dlp."""

import re
from typing import Dict, List
import yt_dlp


def extract_playlist_id(url: str) -> str:
    """Extract playlist ID from YouTube URL.
    
    Args:
        url: YouTube playlist URL
        
    Returns:
        Playlist ID
        
    Raises:
        ValueError: If URL is invalid or doesn't contain a playlist ID
    """
    # Match playlist ID from various URL formats
    patterns = [
        r'[?&]list=([a-zA-Z0-9_-]+)',  # Standard format
        r'youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)',  # Direct playlist link
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    raise ValueError(f"Could not extract playlist ID from URL: {url}")


def fetch_playlist_info(playlist_id: str) -> Dict:
    """Fetch playlist metadata using yt-dlp.
    
    Args:
        playlist_id: YouTube playlist ID
        
    Returns:
        Dictionary containing:
            - title: Playlist title
            - description: Playlist description
            - thumbnail: Playlist thumbnail URL
            - channel: Channel name
            - videos: List of video metadata dicts
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,  # Don't download, just get metadata
        'playlistend': 100,  # Limit to first 100 videos for safety
    }
    
    playlist_url = f'https://www.youtube.com/playlist?list={playlist_id}'
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(playlist_url, download=False)
            
            if not info:
                raise ValueError(f"Could not fetch playlist info for ID: {playlist_id}")
            
            # Extract video list
            videos = []
            for idx, entry in enumerate(info.get('entries', []), start=1):
                if entry:  # Skip unavailable videos
                    videos.append({
                        'video_id': entry.get('id'),
                        'title': entry.get('title', 'Untitled'),
                        'duration': entry.get('duration', 0),
                        'thumbnail': entry.get('thumbnail', ''),
                        'order': idx,
                    })
            
            return {
                'playlist_id': playlist_id,
                'title': info.get('title', 'Untitled Playlist'),
                'description': info.get('description', ''),
                'thumbnail': info.get('thumbnail', ''),
                'channel': info.get('uploader', 'Unknown'),
                'video_count': len(videos),
                'videos': videos,
            }
            
        except Exception as e:
            raise ValueError(f"Failed to fetch playlist: {str(e)}")
