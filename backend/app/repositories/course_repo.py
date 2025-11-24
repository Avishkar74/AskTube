"""Course repository for MongoDB operations."""

from typing import List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ..services.playlist_service import extract_playlist_id, fetch_playlist_info
from ..core.logging import logger


async def create_course(db: AsyncIOMotorDatabase, playlist_url: str) -> str:
    """Create a course from a YouTube playlist.
    
    Args:
        db: MongoDB database instance
        playlist_url: YouTube playlist URL
        
    Returns:
        Course ID (string)
    """
    # Extract playlist ID
    playlist_id = extract_playlist_id(playlist_url)
    logger.info(f"Creating course for playlist: {playlist_id}")
    
    # Check if course already exists
    existing = await db.courses.find_one({"playlist_id": playlist_id})
    if existing:
        logger.info(f"Course already exists for playlist {playlist_id}")
        return str(existing["_id"])
    
    # Fetch playlist metadata
    playlist_info = fetch_playlist_info(playlist_id)
    
    # Create course document
    course_doc = {
        "playlist_id": playlist_id,
        "title": playlist_info["title"],
        "description": playlist_info.get("description", ""),
        "thumbnail": playlist_info.get("thumbnail", ""),
        "channel_name": playlist_info.get("channel", ""),
        "video_count": playlist_info["video_count"],
        "videos": playlist_info["videos"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    result = await db.courses.insert_one(course_doc)
    course_id = str(result.inserted_id)
    
    logger.info(f"Created course {course_id} with {len(playlist_info['videos'])} videos")
    
    # Create reports for each video (if they don't exist)
    from ..repositories import report_repo
    for video in playlist_info["videos"]:
        video_id = video["video_id"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Check if report exists
        existing_report = await db.reports.find_one({"video_id": video_id})
        if not existing_report:
            # Create placeholder report
            report_id = await report_repo.insert_report(db, video_url, video_id=video_id)
            logger.info(f"Created report {report_id} for video {video_id}")
            
            # Update course document with report_id
            await db.courses.update_one(
                {"_id": ObjectId(course_id), "videos.video_id": video_id},
                {"$set": {"videos.$.report_id": report_id}}
            )
        else:
            # Link existing report
            await db.courses.update_one(
                {"_id": ObjectId(course_id), "videos.video_id": video_id},
                {"$set": {"videos.$.report_id": str(existing_report["_id"])}}
            )
    
    return course_id


async def get_course(db: AsyncIOMotorDatabase, course_id: str) -> Optional[dict]:
    """Get course by ID with populated video details.
    
    Args:
        db: MongoDB database instance
        course_id: Course ID
        
    Returns:
        Course document or None
    """
    try:
        course = await db.courses.find_one({"_id": ObjectId(course_id)})
        if not course:
            return None
        
        # Convert ObjectId to string
        course["_id"] = str(course["_id"])
        
        # Populate report status for each video
        for video in course.get("videos", []):
            if video.get("report_id"):
                report = await db.reports.find_one({"_id": ObjectId(video["report_id"])})
                if report:
                    video["status"] = report.get("status", "pending")
                    video["processing_error"] = report.get("processing_error")
        
        return course
        
    except Exception as e:
        logger.error(f"Error fetching course {course_id}: {e}")
        return None


async def list_courses(
    db: AsyncIOMotorDatabase,
    limit: int = 50,
    offset: int = 0
) -> List[dict]:
    """List all courses with pagination.
    
    Args:
        db: MongoDB database instance
        limit: Maximum number of courses to return
        offset: Number of courses to skip
        
    Returns:
        List of course documents
    """
    cursor = db.courses.find().sort("created_at", -1).skip(offset).limit(limit)
    courses = await cursor.to_list(length=limit)
    
    # Convert ObjectIds to strings
    for course in courses:
        course["_id"] = str(course["_id"])
    
    return courses


async def count_courses(db: AsyncIOMotorDatabase) -> int:
    """Count total number of courses.
    
    Args:
        db: MongoDB database instance
        
    Returns:
        Total count
    """
    return await db.courses.count_documents({})


async def delete_course(db: AsyncIOMotorDatabase, course_id: str) -> bool:
    """Delete a course (soft delete - keeps reports).
    
    Args:
        db: MongoDB database instance
        course_id: Course ID
        
    Returns:
        True if deleted, False otherwise
    """
    result = await db.courses.delete_one({"_id": ObjectId(course_id)})
    return result.deleted_count > 0
