"""
Jobs Router
Handles job matching and aggregation endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from uuid import UUID, uuid4
from datetime import datetime, timezone
import re
from app.models.schemas import (
    JobMatchRequest,
    JobMatchResponse,
    UserPreferences,
    UserResponse,
    JobUrlSearchRequest,
    JobUrlSearchResponse,
    JobBookmarkResponse
)
from app.patterns.strategy import JobMatchingContext
from app.services.job_aggregation_service import JobAggregationService
from app.services.safe_browsing_service import SafeBrowsingService
from app.services.job_scraper_service import JobScraperService
from app.services.gemini_service import GeminiService
from app.core.singleton import DatabaseManager
from app.core.dependencies import get_current_user_id
from app.patterns.observer import user_event_subject

router = APIRouter()
security = HTTPBearer()


@router.get("/debug-auth")
async def debug_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Debug endpoint to check authentication token
    """
    from app.core.auth import decode_supabase_token, decode_access_token
    token = credentials.credentials
    
    result = {
        "token_length": len(token),
        "token_preview": token[:50] + "..." if len(token) > 50 else token,
        "supabase_decode": None,
        "backend_decode": None,
        "error": None
    }
    
    try:
        supabase_payload = decode_supabase_token(token)
        result["supabase_decode"] = supabase_payload
    except Exception as e:
        result["error"] = f"Supabase decode error: {str(e)}"
    
    try:
        backend_payload = decode_access_token(token)
        result["backend_decode"] = backend_payload
    except Exception as e:
        if not result["error"]:
            result["error"] = f"Backend decode error: {str(e)}"
    
    return result


@router.get("/debug-gemini-models")
async def debug_gemini_models():
    """
    Debug endpoint to list available Gemini models
    """
    try:
        from app.services.gemini_service import GeminiService
        service = GeminiService()
        available_models = service.list_available_models()
        return {
            "available_models": available_models,
            "current_model": service.model.model_name if hasattr(service.model, 'model_name') else "unknown"
        }
    except Exception as e:
        return {
            "error": str(e),
            "available_models": []
        }


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


@router.post("/search-by-url", response_model=JobUrlSearchResponse)
async def search_job_by_url(
    request: JobUrlSearchRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Search and verify a job posting by URL
    
    Flow:
    1. Validate URL format (LinkedIn)
    2. Check Google Safe Browsing API - BLOCK if unsafe
    3. Scrape job data from LinkedIn URL
    4. Create job bookmark immediately
    5. Check user has >= 3 credits
    6. Send scraped data to Gemini API for authenticity analysis
    7. Deduct 3 credits from user
    8. Store Gemini analysis results in job_analyses table
    9. Return combined results (bookmark + analysis)
    """
    db_manager = DatabaseManager.get_instance()
    supabase = db_manager.get_connection()
    
    try:
        # Step 1: Validate URL format (LinkedIn)
        url = request.url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        linkedin_pattern = r'^https?://(www\.)?linkedin\.com/jobs/view/'
        import re
        if not re.match(linkedin_pattern, url):
            raise HTTPException(
                status_code=400,
                detail="Invalid LinkedIn URL format. Expected format: https://www.linkedin.com/jobs/view/..."
            )
        
        # Step 2: Check Google Safe Browsing API - BLOCK if unsafe
        safe_browsing_service = SafeBrowsingService()
        safety_result = await safe_browsing_service.check_url_safety(url)
        # If unsafe, check_url_safety raises HTTPException, so we only get here if safe
        
        # Step 3: Scrape job data from LinkedIn URL
        scraper_service = JobScraperService()
        scraped_data = await scraper_service.scrape_linkedin_job(url)
        
        # Step 4: Create job bookmark immediately
        bookmark_id = uuid4()
        created_at = datetime.now(timezone.utc)
        
        # Determine source enum value
        source_value = scraped_data.get("source", "linkedin").lower()
        if source_value not in ["linkedin", "indeed", "manual"]:
            source_value = "linkedin"
        
        bookmark_insert = {
            "bookmark_id": str(bookmark_id),
            "user_id": str(user_id),
            "title": scraped_data["title"],
            "company": scraped_data["company"],
            "location": scraped_data.get("location"),
            "source": source_value,
            "source_url": scraped_data["source_url"],
            "description": scraped_data.get("description", "")[:5000]  # Truncate if too long
        }
        
        supabase.table("job_bookmarks").insert(bookmark_insert).execute()
        
        # Step 5: Check user has >= 3 credits
        user_response = supabase.table("users").select("credits").eq("user_id", str(user_id)).execute()
        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        current_credits = user_response.data[0].get("credits", 0)
        if current_credits < 3:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient credits. Required: 3, Available: {current_credits}"
            )
        
        # Step 6: Send scraped data to Gemini API for authenticity analysis
        gemini_service = GeminiService()
        authenticity_analysis = await gemini_service.analyze_job_authenticity(
            job_title=scraped_data["title"],
            company=scraped_data["company"],
            location=scraped_data.get("location"),
            description=scraped_data.get("description", "")
        )
        
        # Step 7: Deduct 3 credits from user
        new_credits = current_credits - 3
        supabase.table("users").update({"credits": new_credits}).eq("user_id", str(user_id)).execute()
        
        # Step 8: Store Gemini analysis results in job_analyses table
        analysis_id = uuid4()
        analysis_insert = {
            "analysis_id": str(analysis_id),
            "user_id": str(user_id),
            "job_bookmark_id": str(bookmark_id),
            "is_authentic": authenticity_analysis.get("is_authentic"),
            "confidence_score": float(authenticity_analysis.get("confidence_score", 0.0)),
            "evidence": authenticity_analysis.get("evidence", "")[:5000] if authenticity_analysis.get("evidence") else None,  # Truncate if too long
            "analysis_type": "api_based",
            "credits_used": 3
        }
        
        supabase.table("job_analyses").insert(analysis_insert).execute()
        
        # Step 9: Return combined results
        job_bookmark_response = JobBookmarkResponse(
            bookmark_id=bookmark_id,
            user_id=user_id,
            title=scraped_data["title"],
            company=scraped_data["company"],
            location=scraped_data.get("location"),
            source=source_value,
            source_url=scraped_data["source_url"],
            description=scraped_data.get("description", ""),
            created_at=created_at
        )
        
        from app.models.schemas import JobAnalysisResponse
        analysis_response = JobAnalysisResponse(
            analysis_id=analysis_id,
            user_id=user_id,
            job_bookmark_id=bookmark_id,
            confidence_score=authenticity_analysis.get("confidence_score"),
            is_authentic=authenticity_analysis.get("is_authentic"),
            evidence=authenticity_analysis.get("evidence", ""),
            analysis_type="api_based",
            credits_used=3,
            created_at=created_at
        )
        
        return JobUrlSearchResponse(
            bookmark_id=bookmark_id,
            job_data=job_bookmark_response,
            analysis=analysis_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job search by URL failed: {str(e)}")

