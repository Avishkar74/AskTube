"""Course endpoints for playlist/course management."""

from typing import List
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException

from ...core.logging import logger
from ...repositories import course_repo
from ...schemas.course import CourseIn, CourseOut

router = APIRouter()


@router.post(
    "/courses",
    response_model=dict,
    summary="Import a YouTube playlist as a course",
    description="Create a course from a YouTube playlist URL. Videos are processed in the background.",
)
async def create_course(request: Request, background_tasks: BackgroundTasks, payload: CourseIn):
    """Import a playlist and create a course."""
    db = request.app.state.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        logger.info(f"Creating course from playlist: {payload.playlist_url}")
        course_id = await course_repo.create_course(db, payload.playlist_url)
        
        # Optionally trigger background processing for all videos
        if payload.force_reindex:
            # TODO: Queue background processing for all videos in the course
            pass
        
        return {"course_id": course_id}
        
    except ValueError as e:
        logger.error(f"Invalid playlist URL: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating course: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/courses",
    response_model=dict,
    summary="List all courses",
    description="Get a paginated list of all imported courses.",
)
async def list_courses(request: Request, limit: int = 50, offset: int = 0):
    """List all courses with pagination."""
    db = request.app.state.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        courses = await course_repo.list_courses(db, limit=limit, offset=offset)
        total = await course_repo.count_courses(db)
        
        return {"items": courses, "total": total}
        
    except Exception as e:
        logger.error(f"Error listing courses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/courses/{course_id}",
    response_model=CourseOut,
    summary="Get course details",
    description="Fetch a single course with all video details and processing status.",
)
async def get_course(request: Request, course_id: str):
    """Get course by ID."""
    db = request.app.state.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        course = await course_repo.get_course(db, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        return course
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching course {course_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/courses/{course_id}",
    response_model=dict,
    summary="Delete a course",
    description="Delete a course (reports are preserved).",
)
async def delete_course(request: Request, course_id: str):
    """Delete a course."""
    db = request.app.state.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    try:
        deleted = await course_repo.delete_course(db, course_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Course not found")
        
        return {"message": "Course deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting course {course_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
