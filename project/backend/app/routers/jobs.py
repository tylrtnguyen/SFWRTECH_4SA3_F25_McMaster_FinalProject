"""
Jobs Router
Handles job matching and aggregation endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
import logging
import json
from app.models.schemas import (
    JobMatchRequest,
    JobMatchResponse,
    UserPreferences,
    UserResponse,
    JobUrlSearchRequest,
    JobUrlSearchResponse,
    JobBookmarkResponse,
    JobManualSubmitRequest,
    ExtractedJobData,
    ApplicationStatus,
    JobAnalysisResponse,
    JobIndustryResponse
)
from app.patterns.strategy import JobMatchingContext
from app.services.job_aggregation_service import JobAggregationService
from app.services.safe_browsing_service import SafeBrowsingService
from app.services.job_scraper_service import JobScraperService
from app.services.gemini_service import GeminiService
from app.services.document_service import DocumentService
from app.services.job_document_analysis_service import JobDocumentAnalysisService
from app.core.singleton import DatabaseManager
from app.core.dependencies import get_current_user_id
from app.patterns.observer import user_event_subject

router = APIRouter()
security = HTTPBearer()


logger = logging.getLogger(__name__)

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


@router.get("/industries", response_model=List[JobIndustryResponse])
async def get_industries():
    """
    Get all available job industries for dropdown selection
    """
    db_manager = DatabaseManager.get_instance()
    supabase = db_manager.get_connection()

    try:
        response = supabase.table("job_industry").select("*").order("description").execute()

        industries = []
        for item in response.data:
            industries.append(JobIndustryResponse(
                id=item["id"],
                description=item["description"],
                created_at=datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")) if isinstance(item["created_at"], str) else item["created_at"]
            ))

        return industries
    except Exception as e:
        logger.error(f"Error fetching industries: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch industries: {str(e)}")


@router.post("/industries")
async def add_industry(description: str):
    """
    Add a new industry to the database
    """
    if not description or not description.strip():
        raise HTTPException(status_code=400, detail="Industry description cannot be empty")

    db_manager = DatabaseManager.get_instance()
    supabase = db_manager.get_connection()

    try:
        # Check if industry already exists
        existing = supabase.table("job_industry").select("id").eq("description", description.strip()).execute()
        if existing.data and len(existing.data) > 0:
            return {"message": "Industry already exists", "id": existing.data[0]["id"]}

        # Add new industry
        response = supabase.table("job_industry").insert({
            "description": description.strip()
        }).execute()

        return {
            "message": "Industry added successfully",
            "id": response.data[0]["id"] if response.data else None
        }
    except Exception as e:
        logger.error(f"Error adding industry: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add industry: {str(e)}")


@router.get("/bookmarks", response_model=List[JobBookmarkResponse])
async def get_user_bookmarks(current_user_id: UUID = Depends(get_current_user_id)):
    """
    Get all bookmarks for the current user with analysis data
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()

        # Get bookmarks with analysis data using a join
        response = supabase.table("job_bookmarks").select("""
            *,
            job_industry(description),
            job_analyses(
                analysis_id,
                is_authentic,
                confidence_score,
                evidence,
                analysis_type,
                credits_used,
                created_at
            )
        """).eq("user_id", str(current_user_id)).order("created_at", desc=True).execute()

        if not response.data:
            return []

        bookmarks = []
        for item in response.data:
            # Get analysis data
            analyses = item.get("job_analyses", [])
            latest_analysis = None
            if analyses:
                # Get the most recent analysis
                latest_analysis = max(analyses, key=lambda x: x.get("created_at", ""))

            bookmark = JobBookmarkResponse(
                bookmark_id=UUID(item["bookmark_id"]),
                user_id=current_user_id,
                title=item["title"],
                company=item["company"],
                location=item.get("location"),
                source=item["source"],
                source_url=item.get("source_url"),
                description=item.get("description", ""),
                application_status=ApplicationStatus(item.get("application_status", "interested")),
                created_at=datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")) if isinstance(item["created_at"], str) else item["created_at"],
                job_industry_id=item.get("job_industry_id"),
                # Include analysis data if available
                is_authentic=latest_analysis.get("is_authentic") if latest_analysis else None,
                confidence_score=latest_analysis.get("confidence_score") if latest_analysis else None,
                analysis_evidence=latest_analysis.get("evidence") if latest_analysis else None,
                analysis_type=latest_analysis.get("analysis_type") if latest_analysis else None
            )

            bookmarks.append(bookmark)

        return bookmarks

    except Exception as e:
        logger.error(f"Failed to get user bookmarks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get bookmarks: {str(e)}")


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
    Search and verify a job posting by URL (supports LinkedIn and Indeed)
    
    Flow:
    1. Validate URL format (LinkedIn or Indeed)
    2. Check if job is already bookmarked by this user (by source_url)
    3. If already bookmarked: return existing bookmark and analysis (no credits used)
    4. Check Google Safe Browsing API - BLOCK if unsafe
    5. Scrape job data from URL (platform-specific extraction)
    6. Check user has >= 3 credits
    7. Send scraped data to Gemini API for authenticity analysis
    8. Deduct 3 credits from user
    9. ONLY if job is genuine (is_authentic=true): Create job bookmark with Gemini-extracted data
    10. Store Gemini analysis results in job_analyses table
    11. Return combined results (with bookmarked flag)
    """
    db_manager = DatabaseManager.get_instance()
    supabase = db_manager.get_connection()
    
    try:
        # Step 1: Validate and normalize URL format (LinkedIn or Indeed)
        url = request.url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        # Step 2: Check if job is already bookmarked by this user
        existing_bookmark = supabase.table("job_bookmarks").select("*").eq(
            "user_id", str(user_id)
        ).eq("source_url", url).execute()
        
        if existing_bookmark.data and len(existing_bookmark.data) > 0:
            # Job already bookmarked - return existing data without using credits
            bookmark_data = existing_bookmark.data[0]
            bookmark_id = UUID(bookmark_data["bookmark_id"])
            
            # Fetch the latest analysis for this bookmark
            existing_analysis = supabase.table("job_analyses").select("*").eq(
                "job_bookmark_id", str(bookmark_id)
            ).order("created_at", desc=True).limit(1).execute()
            
            # Build bookmark response
            job_bookmark_response = JobBookmarkResponse(
                bookmark_id=bookmark_id,
                user_id=user_id,
                title=bookmark_data["title"],
                company=bookmark_data["company"],
                location=bookmark_data.get("location"),
                source=bookmark_data["source"],
                source_url=bookmark_data.get("source_url"),
                description=bookmark_data.get("description"),
                application_status=ApplicationStatus(bookmark_data.get("application_status", "interested")),
                created_at=datetime.fromisoformat(bookmark_data["created_at"].replace("Z", "+00:00")) if isinstance(bookmark_data["created_at"], str) else bookmark_data["created_at"]
            )
            
            # Build analysis response from existing data
            if existing_analysis.data and len(existing_analysis.data) > 0:
                analysis_data = existing_analysis.data[0]
                analysis_response = JobAnalysisResponse(
                    analysis_id=UUID(analysis_data["analysis_id"]),
                    user_id=user_id,
                    job_bookmark_id=bookmark_id,
                    confidence_score=analysis_data.get("confidence_score"),
                    is_authentic=analysis_data.get("is_authentic"),
                    evidence=analysis_data.get("evidence", ""),
                    analysis_type=analysis_data.get("analysis_type", "api_based"),
                    credits_used=0,  # No credits used for existing bookmark
                    created_at=datetime.fromisoformat(analysis_data["created_at"].replace("Z", "+00:00")) if isinstance(analysis_data["created_at"], str) else analysis_data["created_at"],
                    extracted_data=None
                )
            else:
                # No analysis found - create a placeholder response
                analysis_response = JobAnalysisResponse(
                    analysis_id=uuid4(),
                    user_id=user_id,
                    job_bookmark_id=bookmark_id,
                    confidence_score=None,
                    is_authentic=True,  # Assume authentic since it was bookmarked
                    evidence="This job was previously bookmarked. No new analysis was performed.",
                    analysis_type="existing",
                    credits_used=0,
                    created_at=datetime.now(timezone.utc),
                    extracted_data=None
                )
            
            return JobUrlSearchResponse(
                bookmarked=True,
                already_bookmarked=True,
                bookmark_id=bookmark_id,
                job_data=job_bookmark_response,
                analysis=analysis_response
            )
        
        # Step 3: Check Google Safe Browsing API - BLOCK if unsafe
        safe_browsing_service = SafeBrowsingService()
        safety_result = await safe_browsing_service.check_url_safety(url)
        # If unsafe, check_url_safety raises HTTPException, so we only get here if safe
        
        # Step 4: Scrape job data from URL (supports LinkedIn and Indeed)
        scraper_service = JobScraperService()
        scraped_data = await scraper_service.scrape_job_data(url)
        
        # Step 5: Check user has >= 3 credits BEFORE analysis
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
        
        # Extract Gemini's extracted_data for enhanced job info
        extracted_data = authenticity_analysis.get("extracted_data", {})
        is_authentic = authenticity_analysis.get("is_authentic", False)
        
        # Determine source enum value
        source_value = scraped_data.get("source", "linkedin").lower()
        if source_value not in ["linkedin", "indeed", "manual"]:
            source_value = "linkedin"

        # Look up industry ID
        industry_id = None
        if request.industry:
            try:
                industry_response = supabase.table("job_industry").select("id").eq("description", request.industry.strip()).execute()
                if industry_response.data and len(industry_response.data) > 0:
                    industry_id = industry_response.data[0]["id"]
            except Exception as e:
                logger.warning(f"Could not find industry '{request.industry}': {str(e)}")
        
        created_at = datetime.now(timezone.utc)
        bookmark_id = None
        job_bookmark_response = None
        
        # Step 8: ONLY create bookmark if job is genuine (is_authentic=true)
        if is_authentic:
            bookmark_id = uuid4()
            
            # Use Gemini-extracted data to enhance the bookmark
            # Priority: Gemini extracted > scraped data
            final_company = extracted_data.get("company") or scraped_data["company"]
            final_location = extracted_data.get("location") or scraped_data.get("location")
            
            bookmark_insert = {
                "bookmark_id": str(bookmark_id),
                "user_id": str(user_id),
                "title": scraped_data["title"],
                "company": final_company,
                "location": final_location,
                "source": source_value,
                "source_url": scraped_data["source_url"],
                "description": scraped_data.get("description", "")[:5000],  # Truncate if too long
                "application_status": "interested"
            }
            
            supabase.table("job_bookmarks").insert(bookmark_insert).execute()
            
            job_bookmark_response = JobBookmarkResponse(
                bookmark_id=bookmark_id,
                user_id=user_id,
                title=scraped_data["title"],
                company=final_company,
                location=final_location,
                source=source_value,
                source_url=scraped_data["source_url"],
                description=scraped_data.get("description", ""),
                application_status=ApplicationStatus.INTERESTED,
                created_at=created_at
            )
        
        # Step 9: Store Gemini analysis results in job_analyses table
        analysis_id = uuid4()
        analysis_insert = {
            "analysis_id": str(analysis_id),
            "user_id": str(user_id),
            "job_bookmark_id": str(bookmark_id) if bookmark_id else None,
            "is_authentic": is_authentic,
            "confidence_score": float(authenticity_analysis.get("confidence_score", 0.0)),
            "evidence": authenticity_analysis.get("evidence", "")[:5000] if authenticity_analysis.get("evidence") else None,
            "analysis_type": "api_based",
            "credits_used": 3
        }
        
        supabase.table("job_analyses").insert(analysis_insert).execute()
        
        # Step 10: Return combined results with bookmarked flag
        # Create extracted_data response object
        extracted_data_response = ExtractedJobData(
            company=extracted_data.get("company"),
            location=extracted_data.get("location"),
            industry=extracted_data.get("industry")
        ) if extracted_data else None
        
        analysis_response = JobAnalysisResponse(
            analysis_id=analysis_id,
            user_id=user_id,
            job_bookmark_id=bookmark_id,
            confidence_score=authenticity_analysis.get("confidence_score"),
            is_authentic=is_authentic,
            evidence=authenticity_analysis.get("evidence", ""),
            analysis_type="api_based",
            credits_used=3,
            created_at=created_at,
            extracted_data=extracted_data_response
        )
        
        return JobUrlSearchResponse(
            bookmarked=is_authentic,
            already_bookmarked=False,
            bookmark_id=bookmark_id,
            job_data=job_bookmark_response,
            analysis=analysis_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job search by URL failed: {str(e)}")


@router.post("/submit-manual", response_model=JobUrlSearchResponse)
async def submit_manual_job(
    request: JobManualSubmitRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Submit and verify a manually entered job posting

    Flow:
    1. Check user has >= 3 credits
    2. Check if job with same title/company already exists for this user
    3. Send job data to Gemini API for authenticity analysis
    4. Deduct 3 credits from user
    5. ONLY if job is genuine (is_authentic=true): Create job bookmark
    6. Store Gemini analysis results in job_analyses table
    7. Return combined results (with bookmarked flag)
    """
    logger = logging.getLogger(__name__)

    db_manager = DatabaseManager.get_instance()
    supabase = db_manager.get_connection()


    try:
        # Step 1: Check user has >= 3 credits BEFORE analysis
        user_response = supabase.table("users").select("credits").eq("user_id", str(user_id)).execute()

        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")

        current_credits = user_response.data[0].get("credits", 0)

        if current_credits < 3:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient credits. Required: 3, Available: {current_credits}"
            )


        # Step 2: Check if job with same title/company already exists for this user
        existing_bookmark = supabase.table("job_bookmarks").select("*").eq(
            "user_id", str(user_id)
        ).eq("title", request.job_title).eq("company", request.company).execute()


        if existing_bookmark.data and len(existing_bookmark.data) > 0:
            # Job already exists - return existing data without using credits
            bookmark_data = existing_bookmark.data[0]
            bookmark_id = UUID(bookmark_data["bookmark_id"])

            # Fetch the latest analysis for this bookmark
            existing_analysis = supabase.table("job_analyses").select("*").eq(
                "job_bookmark_id", str(bookmark_id)
            ).order("created_at", desc=True).limit(1).execute()


            # Build bookmark response
            job_bookmark_response = JobBookmarkResponse(
                bookmark_id=bookmark_id,
                user_id=user_id,
                title=bookmark_data["title"],
                company=bookmark_data["company"],
                location=bookmark_data.get("location"),
                source=bookmark_data["source"],
                source_url=bookmark_data.get("source_url"),
                description=bookmark_data.get("description"),
                application_status=ApplicationStatus(bookmark_data.get("application_status", "interested")),
                created_at=datetime.fromisoformat(bookmark_data["created_at"].replace("Z", "+00:00")) if isinstance(bookmark_data["created_at"], str) else bookmark_data["created_at"]
            )

            # Build analysis response from existing data
            if existing_analysis.data and len(existing_analysis.data) > 0:
                analysis_data = existing_analysis.data[0]
                analysis_response = JobAnalysisResponse(
                    analysis_id=UUID(analysis_data["analysis_id"]),
                    user_id=user_id,
                    job_bookmark_id=bookmark_id,
                    confidence_score=analysis_data.get("confidence_score"),
                    is_authentic=analysis_data.get("is_authentic"),
                    evidence=analysis_data.get("evidence", ""),
                    analysis_type=analysis_data.get("analysis_type", "api_based"),
                    credits_used=0,  # No credits used for existing job
                    created_at=datetime.fromisoformat(analysis_data["created_at"].replace("Z", "+00:00")) if isinstance(analysis_data["created_at"], str) else analysis_data["created_at"],
                    extracted_data=None
                )
            else:
                # No analysis found - create a placeholder response
                analysis_response = JobAnalysisResponse(
                    analysis_id=uuid4(),
                    user_id=user_id,
                    job_bookmark_id=bookmark_id,
                    confidence_score=None,
                    is_authentic=True,  # Assume authentic since it was bookmarked
                    evidence="This job was previously submitted. No new analysis was performed.",
                    analysis_type="existing",
                    credits_used=0,
                    created_at=datetime.now(timezone.utc),
                    extracted_data=None
                )

            return JobUrlSearchResponse(
                bookmarked=True,
                already_bookmarked=True,
                bookmark_id=bookmark_id,
                job_data=job_bookmark_response,
                analysis=analysis_response
            )

        # Step 3: Send job data to Gemini API for authenticity analysis
        gemini_service = GeminiService()
        authenticity_analysis = await gemini_service.analyze_job_authenticity(
            job_title=request.job_title,
            company=request.company,
            location=request.location,
            description=request.description
        )


        # Step 4: Deduct 3 credits from user
        new_credits = current_credits - 3
        supabase.table("users").update({"credits": new_credits}).eq("user_id", str(user_id)).execute()

        # Extract Gemini's extracted_data for enhanced job info
        extracted_data = authenticity_analysis.get("extracted_data", {})
        is_authentic = authenticity_analysis.get("is_authentic", False)


        created_at = datetime.now(timezone.utc)
        bookmark_id = None
        job_bookmark_response = None

        # Step 5: ONLY create bookmark if job is genuine (is_authentic=true)
        if is_authentic:
            bookmark_id = uuid4()

            # Use Gemini-extracted data to enhance the bookmark
            # Priority: Gemini extracted > manual input
            final_company = extracted_data.get("company") or request.company
            final_location = extracted_data.get("location") or request.location

            # Look up industry ID
            industry_id = None
            if request.industry:
                try:
                    industry_response = supabase.table("job_industry").select("id").eq("description", request.industry.strip()).execute()
                    if industry_response.data and len(industry_response.data) > 0:
                        industry_id = industry_response.data[0]["id"]
                except Exception as e:
                    logger.warning(f"Could not find industry '{request.industry}': {str(e)}")

            bookmark_insert = {
                "bookmark_id": str(bookmark_id),
                "user_id": str(user_id),
                "title": request.job_title,
                "company": final_company,
                "location": final_location,
                "source": request.source or "manual",
                "source_url": None,  # Manual entries don't have URLs
                "description": request.description[:5000],  # Truncate if too long
                "application_status": "interested",
                "job_industry_id": industry_id
            }

            supabase.table("job_bookmarks").insert(bookmark_insert).execute()

            job_bookmark_response = JobBookmarkResponse(
                bookmark_id=bookmark_id,
                user_id=user_id,
                title=request.job_title,
                company=final_company,
                location=final_location,
                source=request.source or "manual",
                source_url=None,
                description=request.description,
                application_status=ApplicationStatus.INTERESTED,
                job_industry_id=industry_id,
                created_at=created_at
            )

        # Step 6: Store Gemini analysis results in job_analyses table
        analysis_id = uuid4()
        analysis_insert = {
            "analysis_id": str(analysis_id),
            "user_id": str(user_id),
            "job_bookmark_id": str(bookmark_id) if bookmark_id else None,
            "is_authentic": is_authentic,
            "confidence_score": float(authenticity_analysis.get("confidence_score", 0.0)),
            "evidence": authenticity_analysis.get("evidence", "")[:5000] if authenticity_analysis.get("evidence") else None,
            "analysis_type": "api_based",
            "credits_used": 3
        }

        supabase.table("job_analyses").insert(analysis_insert).execute()

        # Step 7: Return combined results with bookmarked flag
        # Create extracted_data response object
        extracted_data_response = ExtractedJobData(
            company=extracted_data.get("company"),
            location=extracted_data.get("location"),
            industry=extracted_data.get("industry")
        ) if extracted_data else None

        analysis_response = JobAnalysisResponse(
            analysis_id=analysis_id,
            user_id=user_id,
            job_bookmark_id=bookmark_id,
            confidence_score=authenticity_analysis.get("confidence_score"),
            is_authentic=is_authentic,
            evidence=authenticity_analysis.get("evidence", ""),
            analysis_type="api_based",
            credits_used=3,
            created_at=created_at,
            extracted_data=extracted_data_response
        )

        final_response = JobUrlSearchResponse(
            bookmarked=is_authentic,
            already_bookmarked=False,
            bookmark_id=bookmark_id,
            job_data=job_bookmark_response,
            analysis=analysis_response
        )
        return final_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manual job submission failed: {str(e)}")


@router.post("/upload-job-document", response_model=JobUrlSearchResponse)
async def upload_job_document(
    file: UploadFile = File(...),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Upload and analyze a job document (PDF, DOC, DOCX, TXT)

    Process:
    1. Validate file type and size (max 20MB)
    2. Extract text from document
    3. Analyze with Gemini AI for authenticity and details
    4. Store document and analysis results
    5. Create job bookmark if authentic
    6. Return analysis results
    """
    logger = logging.getLogger(__name__)

    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        logger.info(f"Processing document upload: {file.filename} ({file_size} bytes) for user {user_id}")

        # Validate file
        doc_service = DocumentService()
        is_valid, error_msg = doc_service.validate_file(
            file_content, file.filename, file.content_type
        )

        if not is_valid:
            logger.warning(f"File validation failed for {file.filename}: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

        # Check credits before processing
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()

        user_response = supabase.table("users").select("credits").eq("user_id", str(user_id)).execute()
        if not user_response.data or user_response.data[0]["credits"] < 3:
            raise HTTPException(status_code=400, detail="Insufficient credits (3 required)")

        # Deduct credits upfront
        supabase.table("users").update({
            "credits": user_response.data[0]["credits"] - 3
        }).eq("user_id", str(user_id)).execute()

        # Extract text from document
        logger.info(f"Extracting text from {file.filename}")
        extracted_text, metadata = doc_service.extract_text(
            file_content, file.content_type, file.filename
        )

        logger.info(f"Text extracted from {file.filename}: {len(extracted_text)} characters, {metadata.get('words', 0)} words")

        # Generate object ID for storage (placeholder - would integrate with GCP)
        object_id = f"job_docs/{user_id}/{uuid4()}/{file.filename}"

        # Store document record initially with pending status
        doc_data = {
            "user_id": str(user_id),
            "filename": file.filename,
            "file_size": file_size,
            "mime_type": file.content_type,
            "object_id": object_id,
            "extracted_text": extracted_text[:10000],  # Truncate for DB
            "processing_status": "processing",
            "analysis_result": None,
            "processed_at": None
        }

        result = supabase.table("job_documents").insert(doc_data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create document record")

        doc_id = result.data[0]["id"]
        logger.info(f"Document record created with ID {doc_id}")

        # Analyze with Gemini
        analysis_service = JobDocumentAnalysisService()
        analysis_result = await analysis_service.analyze_job_document(
            extracted_text, file.filename, str(user_id), metadata
        )

        logger.info(f"Gemini analysis completed for {file.filename}: authentic={analysis_result.get('is_authentic')}")

        # Update document record with results
        supabase.table("job_documents").update({
            "processing_status": "completed",
            "analysis_result": json.dumps(analysis_result),
            "processed_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", str(doc_id)).execute()

        # Create bookmark if authentic
        bookmark_id = None
        job_data = None

        if analysis_result.get("is_authentic"):
            extracted_data = analysis_result.get("extracted_data", {})

            bookmark_data = {
                "bookmark_id": str(uuid4()),
                "user_id": str(user_id),
                "title": extracted_data.get("title", f"Job from {file.filename}"),
                "company": extracted_data.get("company", "Unknown Company"),
                "location": extracted_data.get("location"),
                "source": "document_upload",
                "source_url": None,  # Document uploads don't have URLs
                "description": extracted_text[:5000],  # Truncate for bookmark
                "application_status": "interested"
            }

            # Look up industry ID if available
            industry_name = extracted_data.get("industry")
            if industry_name:
                try:
                    industry_response = supabase.table("job_industry").select("id").eq("description", industry_name.strip()).execute()
                    if industry_response.data and len(industry_response.data) > 0:
                        bookmark_data["job_industry_id"] = industry_response.data[0]["id"]
                except Exception as e:
                    logger.warning(f"Could not find industry '{industry_name}': {str(e)}")

            bookmark_result = supabase.table("job_bookmarks").insert(bookmark_data).execute()
            if bookmark_result.data:
                bookmark_id = bookmark_result.data[0]["bookmark_id"]
                job_data = JobBookmarkResponse(**bookmark_result.data[0])
                logger.info(f"Job bookmark created with ID {bookmark_id}")

        # Store analysis in job_analyses table
        analysis_record = {
            "analysis_id": str(uuid4()),
            "user_id": str(user_id),
            "job_bookmark_id": bookmark_id,
            "is_authentic": analysis_result.get("is_authentic"),
            "confidence_score": float(analysis_result.get("confidence_score", 0.0)),
            "evidence": analysis_result.get("evidence", "")[:5000],
            "analysis_type": "document_upload",
            "credits_used": 3
        }

        supabase.table("job_analyses").insert(analysis_record).execute()
        logger.info(f"Analysis record stored for document {doc_id}")

        # Return response

        # Create extracted_data response object
        extracted_data = analysis_result.get("extracted_data", {})
        extracted_data_response = ExtractedJobData(
            company=extracted_data.get("company"),
            location=extracted_data.get("location"),
            industry=extracted_data.get("industry")
        ) if extracted_data else None

        analysis_response = JobAnalysisResponse(
            analysis_id=UUID(analysis_record["analysis_id"]),
            user_id=user_id,
            job_bookmark_id=UUID(bookmark_id) if bookmark_id else None,
            confidence_score=analysis_result.get("confidence_score"),
            is_authentic=analysis_result.get("is_authentic"),
            evidence=analysis_result.get("evidence", ""),
            analysis_type="document_upload",
            credits_used=3,
            created_at=datetime.now(timezone.utc),
            extracted_data=extracted_data_response
        )

        response = JobUrlSearchResponse(
            bookmarked=bool(bookmark_id),
            already_bookmarked=False,
            bookmark_id=UUID(bookmark_id) if bookmark_id else None,
            job_data=job_data,
            analysis=analysis_response
        )

        logger.info(f"Document upload completed for {file.filename}: bookmarked={bool(bookmark_id)}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job document upload failed for {file.filename}: {str(e)}")
        # Try to mark document as failed if it was created
        try:
            if 'doc_id' in locals():
                supabase.table("job_documents").update({
                    "processing_status": "failed",
                    "analysis_result": json.dumps({"error": str(e)})
                }).eq("id", str(doc_id)).execute()
        except Exception as update_error:
            logger.error(f"Failed to update document status: {str(update_error)}")

        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

