"""
Analysis Router
Handles job fraud analysis using Chain of Responsibility pattern
"""

from fastapi import APIRouter, HTTPException
from uuid import UUID
from uuid import uuid4
from datetime import datetime, timezone
from app.models.schemas import (
    JobAnalysisRequest,
    JobAnalysisResponse,
    JobAnalysisRequestInternal
)
from app.patterns.chain_of_responsibility import (
    JobAnalysisPipeline,
    FraudDetectionHandler,
    JobScoringHandler,
    SuggestionHandler
)
from app.core.singleton import DatabaseManager
from app.patterns.observer import user_event_subject, EventType

router = APIRouter()


@router.post("/analyze", response_model=JobAnalysisResponse)
async def analyze_job(request: JobAnalysisRequest, user_id: UUID):
    """
    Analyze a job posting for fraud, scoring, and suggestions
    
    Uses Chain of Responsibility pattern to process through:
    1. Fraud Detection
    2. Job Scoring
    3. Suggestion Generation
    """
    try:
        # Get job details from database
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        job_response = supabase.table("jobs").select(
            "job_id, title, company, location, source, source_url, description, posted_date, created_at"
        ).eq("job_id", str(request.job_id)).execute()
        if not job_response.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = job_response.data[0]
        
        # Create internal request for Chain of Responsibility handlers
        internal_request = JobAnalysisRequestInternal(
            job_title=job.get("title", ""),
            company_name=job.get("company", ""),
            job_description=job.get("description", "") or job.get("source_url", ""),  # Use description if available, fallback to source_url
            location=job.get("location"),
            salary_min=None,  # Not in jobs table schema
            salary_max=None,  # Not in jobs table schema
            requirements=None  # Not in jobs table schema
        )
        
        # Build the analysis pipeline using Chain of Responsibility
        pipeline = JobAnalysisPipeline()
        pipeline.add_handler(FraudDetectionHandler())
        pipeline.add_handler(JobScoringHandler())
        pipeline.add_handler(SuggestionHandler())
        
        # Process the request through the chain
        analysis_result = await pipeline.process(internal_request)
        
        # Store analysis in database
        analysis_id = uuid4()
        created_at = datetime.now(timezone.utc)
        
        supabase.table("job_analyses").insert({
            "analysis_id": str(analysis_id),
            "user_id": str(user_id),
            "job_id": str(request.job_id),
            "fraud_score": float(analysis_result.fraud_score) if analysis_result.fraud_score else None,
            "analysis_type": request.analysis_type,
            "credits_used": 2
        }).execute()
        
        # Convert analysis result to response format
        response = JobAnalysisResponse(
            analysis_id=analysis_id,
            user_id=user_id,
            job_id=request.job_id,
            fraud_score=analysis_result.fraud_score,
            analysis_type=request.analysis_type,
            credits_used=2,
            created_at=created_at
        )
        
        # Notify observers using Observer pattern
        await user_event_subject.score_updated(
            user_id=int(str(user_id).replace("-", "")[:8], 16) if isinstance(user_id, UUID) else user_id,
            job_id=str(request.job_id),
            fraud_score=analysis_result.fraud_score or 0.0,
            match_score=analysis_result.match_score or 0.0
        )
        
        await user_event_subject.job_analysis_complete(
            user_id=int(str(user_id).replace("-", "")[:8], 16) if isinstance(user_id, UUID) else user_id,
            job_id=str(request.job_id),
            analysis_result=analysis_result.dict()
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job analysis failed: {str(e)}")


@router.get("/history/{user_id}")
async def get_analysis_history(user_id: UUID, limit: int = 10):
    """
    Get job analysis history for a user
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        response = supabase.table("job_analyses").select(
            "analysis_id, job_id, fraud_score, created_at"
        ).eq("user_id", str(user_id)).order("created_at", desc=True).limit(limit).execute()
        
        analyses = []
        for row in response.data:
            analyses.append({
                "id": row["analysis_id"],
                "job_id": row["job_id"],
                "fraud_score": row["fraud_score"],
                "created_at": row["created_at"]
            })
        
        return {
            "user_id": user_id,
            "analyses": analyses,
            "total": len(analyses)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis history: {str(e)}")

