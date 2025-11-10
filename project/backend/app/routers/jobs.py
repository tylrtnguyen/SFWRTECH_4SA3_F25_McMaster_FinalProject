"""
Jobs Router
Handles job matching and aggregation endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.schemas import (
    JobMatchRequest,
    JobMatchResponse,
    UserPreferences,
    UserResponse
)
from app.patterns.strategy import JobMatchingContext
from app.services.job_aggregation_service import JobAggregationService
from app.core.singleton import DatabaseManager
from app.patterns.observer import user_event_subject

router = APIRouter()


def get_user_preferences(user_id: int) -> UserPreferences:
    """Get user preferences from database"""
    db_manager = DatabaseManager.get_instance()
    supabase = db_manager.get_connection()
    
    # In a real implementation, this would fetch from a user_preferences table
    # For now, return default preferences
    return UserPreferences(
        min_salary=60000,
        preferred_locations=[],
        skills=["Python", "FastAPI"],
        job_types=[]
    )


@router.post("/match", response_model=JobMatchResponse)
async def match_jobs(request: JobMatchRequest):
    """
    Match jobs based on user preferences and selected strategy
    
    Uses Strategy pattern to switch between different matching algorithms
    """
    try:
        # Get user preferences
        user_preferences = get_user_preferences(request.user_id)
        
        # Aggregate jobs from multiple sources
        job_service = JobAggregationService()
        available_jobs = await job_service.aggregate_jobs(
            keywords="software engineer",
            location=None,
            limit=50
        )
        
        # Get matching strategy
        strategy = JobMatchingContext.get_strategy_by_name(request.strategy)
        context = JobMatchingContext(strategy)
        
        # Execute matching
        matches = await context.execute_matching(user_preferences, available_jobs)
        
        # Limit results
        limited_matches = matches[:request.limit]
        
        # Format response
        formatted_matches = [
            {
                "job": {
                    "id": match["job"].id,
                    "title": match["job"].title,
                    "company_name": match["job"].company_name,
                    "location": match["job"].location,
                    "salary_max": match["job"].salary_max,
                    "source": match["job"].source
                },
                "match_score": match["score"],
                "strategy": match["strategy"]
            }
            for match in limited_matches
        ]
        
        return JobMatchResponse(
            matches=formatted_matches,
            strategy_used=request.strategy,
            total_jobs=len(available_jobs)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job matching failed: {str(e)}")


@router.get("/aggregate")
async def aggregate_jobs(
    keywords: str = None,
    location: str = None,
    sources: str = "linkedin,indeed",
    limit: int = 20
):
    """
    Aggregate jobs from LinkedIn and Indeed feeds
    """
    try:
        job_service = JobAggregationService()
        source_list = [s.strip() for s in sources.split(",")]
        
        jobs = await job_service.aggregate_jobs(
            keywords=keywords,
            location=location,
            sources=source_list,
            limit=limit
        )
        
        return {
            "jobs": [job.dict() for job in jobs],
            "total": len(jobs),
            "sources": source_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job aggregation failed: {str(e)}")

