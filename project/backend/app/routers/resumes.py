"""
Resumes Router
Handles resume CRUD operations, file management, and analysis
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form, Query
from uuid import UUID
from uuid import uuid4
from datetime import datetime, timezone
from typing import List, Optional
from app.models.schemas import (
    ResumeUpdate,
    ResumeResponse,
    ResumeAnalysisResponse,
    ExperienceLevel
)
from app.core.singleton import DatabaseManager
from app.core.dependencies import get_current_user_id
from app.logging_system import logger_manager as logger
from app.services.gcs_service import GCSService

router = APIRouter()

@router.post("/", response_model=ResumeResponse)
async def create_resume(
    file: UploadFile = File(...),
    resume_name: str = Form(...),
    experience: str = Form("junior"),
    targeted_job_bookmark_id: Optional[str] = Form(None),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Upload a new resume file
    
    This endpoint handles:
    1. File upload to GCP Cloud Storage
    2. Database record creation with metadata
    3. Returns resume metadata
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        gcs_service = GCSService.get_instance()
        
        # Validate file type
        allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Only PDF and DOCX files are allowed."
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size (max 20MB)
        max_size = 20 * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is 20MB."
            )
        
        # Generate object ID for GCS
        resume_id = uuid4()
        object_id = f"resumes/{user_id}/{resume_id}/{file.filename}"
        
        # Upload to GCS
        content_type = file.content_type or "application/pdf"
        upload_success = gcs_service.upload_file(file_content, object_id, content_type)
        
        if not upload_success and gcs_service.is_configured():
            logger.warning("GCS upload failed but continuing with database record")
        
        # Parse experience level
        try:
            experience_enum = ExperienceLevel(experience.lower())
        except ValueError:
            experience_enum = ExperienceLevel.JUNIOR
        
        # Parse targeted job bookmark ID
        target_job_id = None
        if targeted_job_bookmark_id and targeted_job_bookmark_id.strip():
            try:
                target_job_id = str(UUID(targeted_job_bookmark_id))
            except ValueError:
                pass
        
        # Create resume record in database
        # Let the database use its DEFAULT NOW() for uploaded_at
        resume_data = {
            "id": str(resume_id),
            "filename": file.filename,
            "size": file_size,
            # uploaded_at will use DEFAULT NOW()
            "object_id": object_id,
            "user_id": str(user_id),
            "resume_name": resume_name,
            "experience": experience_enum.value,
            "targeted_job_bookmark_id": target_job_id
        }
        
        result = supabase.table("resumes").insert(resume_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create resume record")
        
        logger.info(f"Resume created successfully: {resume_id}")
        
        # Get targeted job info if available
        targeted_job_title = None
        targeted_job_company = None
        if target_job_id:
            job_response = supabase.table("job_bookmarks").select("title, company").eq("bookmark_id", target_job_id).execute()
            if job_response.data:
                targeted_job_title = job_response.data[0].get("title")
                targeted_job_company = job_response.data[0].get("company")

        # uploaded_at will use database default (NOW() with timezone)

        return ResumeResponse(
            id=resume_id,
            filename=file.filename,
            size=file_size,
            uploaded_at=datetime.now(timezone.utc),
            object_id=object_id,
            user_id=user_id,
            resume_name=resume_name,
            experience=experience_enum,
            targeted_job_bookmark_id=UUID(target_job_id) if target_job_id else None,
            targeted_job_title=targeted_job_title,
            targeted_job_company=targeted_job_company
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Resume upload failed: {str(e)}")


@router.get("/", response_model=List[ResumeResponse])
async def get_user_resumes(
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get all resumes for the current user
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        # Get resumes with latest analysis data
        response = supabase.table("resumes").select(
            "id, filename, size, uploaded_at, object_id, user_id, resume_name, experience, targeted_job_bookmark_id"
        ).eq("user_id", str(user_id)).order("uploaded_at", desc=True).execute()

        # Get latest analysis for each resume
        resume_ids = [row["id"] for row in response.data] if response.data else []
        analysis_data = {}
        if resume_ids:
            analysis_response = supabase.table("resume_analyses").select(
                "resume_id, match_score, recommended_tips, created_at"
            ).in_("resume_id", resume_ids).order("created_at", desc=True).execute()

            # Group by resume_id, keeping only the latest analysis
            for analysis in analysis_response.data or []:
                resume_id = analysis["resume_id"]
                if resume_id not in analysis_data:
                    analysis_data[resume_id] = analysis
        
        resumes = []
        for row in response.data:
            # Get targeted job info if available
            targeted_job_title = None
            targeted_job_company = None
            if row.get("targeted_job_bookmark_id"):
                job_response = supabase.table("job_bookmarks").select("title, company").eq("bookmark_id", row["targeted_job_bookmark_id"]).execute()
                if job_response.data:
                    targeted_job_title = job_response.data[0].get("title")
                    targeted_job_company = job_response.data[0].get("company")

            # Get analysis data for this resume
            analysis = analysis_data.get(row["id"])
            match_score = analysis.get("match_score") if analysis else None
            recommended_tips = analysis.get("recommended_tips") if analysis else None

            resumes.append(ResumeResponse(
                id=UUID(row["id"]),
                filename=row["filename"],
                size=row["size"],
                uploaded_at=datetime.fromisoformat(row["uploaded_at"]) if isinstance(row["uploaded_at"], str) else row["uploaded_at"],
                object_id=row["object_id"],
                user_id=UUID(row["user_id"]),
                resume_name=row.get("resume_name") or row["filename"],
                experience=ExperienceLevel(row["experience"]) if row.get("experience") else ExperienceLevel.JUNIOR,
                targeted_job_bookmark_id=UUID(row["targeted_job_bookmark_id"]) if row.get("targeted_job_bookmark_id") else None,
                match_score=match_score,
                recommended_tips=recommended_tips,
                targeted_job_title=targeted_job_title,
                targeted_job_company=targeted_job_company
            ))
        
        return resumes
    except Exception as e:
        logger.error(f"Failed to get resumes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get resumes: {str(e)}")


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get a specific resume by ID
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        # Get resume with latest analysis data
        response = supabase.table("resumes").select(
            "id, filename, size, uploaded_at, object_id, user_id, resume_name, experience, targeted_job_bookmark_id"
        ).eq("id", str(resume_id)).eq("user_id", str(user_id)).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Resume not found")

        row = response.data[0]

        # Get latest analysis for this resume
        analysis_response = supabase.table("resume_analyses").select(
            "match_score, recommended_tips, created_at"
        ).eq("resume_id", str(resume_id)).order("created_at", desc=True).limit(1).execute()

        analysis = analysis_response.data[0] if analysis_response.data else None
        
        # Get targeted job info if available
        targeted_job_title = None
        targeted_job_company = None
        if row.get("targeted_job_bookmark_id"):
            job_response = supabase.table("job_bookmarks").select("title, company").eq("bookmark_id", row["targeted_job_bookmark_id"]).execute()
            if job_response.data:
                targeted_job_title = job_response.data[0].get("title")
                targeted_job_company = job_response.data[0].get("company")
                
        return ResumeResponse(
            id=UUID(row["id"]),
            filename=row["filename"],
            size=row["size"],
                uploaded_at=datetime.fromisoformat(row["uploaded_at"]) if isinstance(row["uploaded_at"], str) else row["uploaded_at"],
            object_id=row["object_id"],
            user_id=UUID(row["user_id"]),
            resume_name=row.get("resume_name") or row["filename"],
            experience=ExperienceLevel(row["experience"]) if row.get("experience") else ExperienceLevel.JUNIOR,
            targeted_job_bookmark_id=UUID(row["targeted_job_bookmark_id"]) if row.get("targeted_job_bookmark_id") else None,
            match_score=analysis.get("match_score") if analysis else None,
            recommended_tips=analysis.get("recommended_tips") if analysis else None,
            targeted_job_title=targeted_job_title,
            targeted_job_company=targeted_job_company
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get resume: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get resume: {str(e)}")


@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: UUID,
    update_data: ResumeUpdate,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Update resume metadata (name, experience, targeted job)
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        # Verify resume belongs to user
        check_response = supabase.table("resumes").select("id").eq("id", str(resume_id)).eq("user_id", str(user_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Build update dict
        update_dict = {}
        if update_data.resume_name is not None:
            update_dict["resume_name"] = update_data.resume_name
        if update_data.experience is not None:
            update_dict["experience"] = update_data.experience.value

        # Handle targeted_job_bookmark_id - check if it was explicitly provided
        # Use getattr to safely access model_fields_set (Pydantic v2)
        fields_set = getattr(update_data, 'model_fields_set', set())
        if 'targeted_job_bookmark_id' in fields_set:
            if update_data.targeted_job_bookmark_id is not None:
                update_dict["targeted_job_bookmark_id"] = str(update_data.targeted_job_bookmark_id)
            else:
                # Explicitly set to null to clear targeting
                update_dict["targeted_job_bookmark_id"] = None
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Update resume
        result = supabase.table("resumes").update(update_dict).eq("id", str(resume_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update resume")
        
        logger.info(f"Resume updated: {resume_id}")
        
        # Return updated resume
        return await get_resume(resume_id, user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update resume: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update resume: {str(e)}")


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Delete a resume (removes file from GCS and database record)
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        gcs_service = GCSService.get_instance()
        
        # Verify resume belongs to user and get object_id
        check_response = supabase.table("resumes").select("id, object_id").eq("id", str(resume_id)).eq("user_id", str(user_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        object_id = check_response.data[0]["object_id"]
        
        # Delete file from GCS
        gcs_service.delete_file(object_id)
        
        # Delete database record
        supabase.table("resumes").delete().eq("id", str(resume_id)).execute()
        
        logger.info(f"Resume deleted: {resume_id}")
        
        return {"success": True, "message": "Resume deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete resume: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete resume: {str(e)}")


@router.post("/{resume_id}/duplicate", response_model=ResumeResponse)
async def duplicate_resume(
    resume_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Duplicate an existing resume
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        gcs_service = GCSService.get_instance()
        
        # Get original resume
        original_response = supabase.table("resumes").select("*").eq("id", str(resume_id)).eq("user_id", str(user_id)).execute()
        if not original_response.data:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        original = original_response.data[0]
        
        # Generate new IDs
        new_resume_id = uuid4()
        new_object_id = f"resumes/{user_id}/{new_resume_id}/{original['filename']}"
        
        # Copy file in GCS
        original_content = gcs_service.get_file_content(original["object_id"])
        if original_content:
            gcs_service.upload_file(original_content, new_object_id)
        
        # Create new resume record
        new_resume_data = {
            "id": str(new_resume_id),
            "filename": original["filename"],
            "size": original["size"],
            # uploaded_at will use DEFAULT NOW()
            "object_id": new_object_id,
            "user_id": str(user_id),
            "resume_name": f"{original.get('resume_name', original['filename'])} (Copy)",
            "experience": original.get("experience", "junior"),
            "targeted_job_bookmark_id": original.get("targeted_job_bookmark_id")
        }
        
        result = supabase.table("resumes").insert(new_resume_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to duplicate resume")
        
        logger.info(f"Resume duplicated: {resume_id} -> {new_resume_id}")
        
        return await get_resume(new_resume_id, user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to duplicate resume: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to duplicate resume: {str(e)}")


@router.get("/{resume_id}/preview-url")
async def get_resume_preview_url(
    resume_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get a signed URL for resume preview (valid for 15 minutes)
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        gcs_service = GCSService.get_instance()
        
        # Verify resume belongs to user
        check_response = supabase.table("resumes").select("object_id").eq("id", str(resume_id)).eq("user_id", str(user_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        object_id = check_response.data[0]["object_id"]
        
        # Generate signed URL
        signed_url = gcs_service.get_signed_url(object_id, expiration_minutes=15)
        
        if not signed_url:
            raise HTTPException(status_code=500, detail="Failed to generate preview URL. GCS may not be configured.")
        
        return {"preview_url": signed_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get preview URL: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get preview URL: {str(e)}")


@router.get("/{resume_id}/download-url")
async def get_resume_download_url(
    resume_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get a signed URL for resume download (valid for 60 minutes)
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        gcs_service = GCSService.get_instance()
        
        # Verify resume belongs to user
        check_response = supabase.table("resumes").select("object_id").eq("id", str(resume_id)).eq("user_id", str(user_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        object_id = check_response.data[0]["object_id"]
        
        # Generate download URL
        download_url = gcs_service.get_download_url(object_id, expiration_minutes=60)
        
        if not download_url:
            raise HTTPException(status_code=500, detail="Failed to generate download URL. GCS may not be configured.")
        
        return {"download_url": download_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get download URL: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get download URL: {str(e)}")


@router.post("/{resume_id}/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(
    resume_id: UUID,
    force: bool = Query(False),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Analyze resume with Gemini AI to get tips and match score

    If resume has a targeted job, analysis includes job-specific recommendations
    and calculates a match score.

    If tips already exist, returns cached results with last_analyzed_at timestamp.
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()

        # Import here to avoid circular imports
        from app.services.resume_analysis_service import ResumeAnalysisService

        # Get resume details
        resume_response = supabase.table("resumes").select(
            "id, object_id, targeted_job_bookmark_id, resume_name"
        ).eq("id", str(resume_id)).eq("user_id", str(user_id)).execute()

        if not resume_response.data:
            raise HTTPException(status_code=404, detail="Resume not found")

        resume_data = resume_response.data[0]

        # Check if analysis already exists for this resume and targeted job combination
        analysis_query = supabase.table("resume_analyses").select(
            "id, match_score, targeted_job_bookmark_id, recommended_tips, created_at"
        ).eq("resume_id", str(resume_id))

        # If resume has a targeted job, look for analysis with that specific job
        # Otherwise, look for any general analysis (targeted_job_bookmark_id is null)
        if resume_data.get("targeted_job_bookmark_id"):
            analysis_query = analysis_query.eq("targeted_job_bookmark_id", resume_data["targeted_job_bookmark_id"])
        else:
            analysis_query = analysis_query.is_("targeted_job_bookmark_id", None)

        analysis_response = analysis_query.order("created_at", desc=True).limit(1).execute()

        # If analysis exists and not forcing refresh, return cached results
        if analysis_response.data and not force:
            analysis_data = analysis_response.data[0]
            logger.info(f"Returning cached analysis for resume: {resume_id}")

            # Get targeted job details if available
            job_title = None
            job_company = None
            if analysis_data.get("targeted_job_bookmark_id"):
                job_response = supabase.table("job_bookmarks").select(
                    "title, company"
                ).eq("bookmark_id", analysis_data["targeted_job_bookmark_id"]).execute()

                if job_response.data:
                    job_title = job_response.data[0].get("title")
                    job_company = job_response.data[0].get("company")

            # Ensure match_score is a valid float, defaulting to 0.0 if None
            cached_match_score = analysis_data.get("match_score")
            if cached_match_score is None:
                cached_match_score = 0.0
            try:
                cached_match_score = float(cached_match_score)
                cached_match_score = max(0.0, min(100.0, cached_match_score))  # Clamp to valid range
            except (ValueError, TypeError):
                logger.warning(f"Invalid cached match_score: {cached_match_score}, defaulting to 0.0")
                cached_match_score = 0.0

            return ResumeAnalysisResponse(
                resume_id=resume_id,
                match_score=cached_match_score,
                recommended_tips=analysis_data["recommended_tips"],
                targeted_job_title=job_title,
                targeted_job_company=job_company,
                credits_used=0,  # No credits used for cached results
                last_analyzed_at=analysis_data["created_at"]
            )
        
        # Check user credits
        user_response = supabase.table("users").select("credits").eq("user_id", str(user_id)).execute()
        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        current_credits = user_response.data[0].get("credits", 0)
        if current_credits < 5:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient credits. Required: 5, Available: {current_credits}"
            )
        
        # Get resume content from GCS
        gcs_service = GCSService.get_instance()
        logger.info(f"Attempting to retrieve file from GCS: {resume_data['object_id']}")
        resume_content = gcs_service.get_file_content(resume_data["object_id"])

        if not resume_content:
            logger.error(f"Failed to retrieve resume file from GCS: {resume_data['object_id']}")
            raise HTTPException(status_code=500, detail="Failed to retrieve resume file from storage")

        logger.info(f"Successfully retrieved resume file, size: {len(resume_content)} bytes")
        
        # Get targeted job details if available
        job_description = None
        job_title = None
        job_company = None
        
        if resume_data.get("targeted_job_bookmark_id"):
            job_response = supabase.table("job_bookmarks").select(
                "title, company, description"
            ).eq("bookmark_id", resume_data["targeted_job_bookmark_id"]).execute()
            
            if job_response.data:
                job_title = job_response.data[0].get("title")
                job_company = job_response.data[0].get("company")
                job_description = job_response.data[0].get("description")
        
        # Analyze resume
        analysis_service = ResumeAnalysisService()
        analysis_result = await analysis_service.analyze_resume(
            resume_content=resume_content,
            job_description=job_description,
            job_title=job_title,
            job_company=job_company
        )

        # Only proceed if analysis was successful (has valid match_score)
        match_score = analysis_result.get("match_score")
        if match_score is None:
            logger.error("Analysis failed: match_score is None")
            raise HTTPException(status_code=500, detail="Analysis failed: invalid match score")

        # Ensure match_score is a valid float
        try:
            match_score = float(match_score)
            match_score = max(0.0, min(100.0, match_score))  # Clamp to valid range
        except (ValueError, TypeError):
            logger.error(f"Analysis failed: invalid match_score value: {match_score}")
            raise HTTPException(status_code=500, detail="Analysis failed: invalid match score format")

        # Deduct credits
        new_credits = current_credits - 5
        supabase.table("users").update({"credits": new_credits}).eq("user_id", str(user_id)).execute()
        logger.info(f"Deducted 5 credits for resume analysis. New balance: {new_credits}",
                   user_id=str(user_id), action="credit_deduct", details={"amount": 5, "new_balance": new_credits})

        # Delete existing analysis records for this resume and job combination
        delete_query = supabase.table("resume_analyses").delete().eq("resume_id", str(resume_id))

        if resume_data.get("targeted_job_bookmark_id"):
            delete_query = delete_query.eq("targeted_job_bookmark_id", resume_data["targeted_job_bookmark_id"])
        else:
            delete_query = delete_query.is_("targeted_job_bookmark_id", None)

        delete_query.execute()
        logger.info(f"Deleted existing analysis records for resume: {resume_id}",
                   user_id=str(user_id), action="resume_reanalyze")

        # Insert new analysis record into resume_analyses table
        analysis_data = {
            "resume_id": str(resume_id),
            "recommended_tips": analysis_result["tips"],
            "targeted_job_bookmark_id": resume_data.get("targeted_job_bookmark_id")
        }

        # Include match_score - set to null if no targeted job, otherwise use the score
        if resume_data.get("targeted_job_bookmark_id"):
            analysis_data["match_score"] = match_score
        else:
            analysis_data["match_score"] = None

        supabase.table("resume_analyses").insert(analysis_data).execute()

        logger.info(f"Resume analyzed: {resume_id}, match_score: {analysis_result['match_score']}",
                   user_id=str(user_id), action="resume_analyze")

        # Get the timestamp of the analysis (use current time since we just inserted)
        from datetime import datetime, timezone
        analysis_timestamp = datetime.now(timezone.utc).isoformat()

        # Return match_score for targeted jobs, 0.0 for general analysis
        response_match_score = match_score if resume_data.get("targeted_job_bookmark_id") else 0.0

        # Ensure response_match_score is a valid float
        try:
            response_match_score = float(response_match_score)
            response_match_score = max(0.0, min(100.0, response_match_score))  # Clamp to valid range
        except (ValueError, TypeError):
            logger.error(f"Invalid response_match_score: {response_match_score}, defaulting to 0.0")
            response_match_score = 0.0

        return ResumeAnalysisResponse(
            resume_id=resume_id,
            match_score=response_match_score,
            recommended_tips=analysis_result["tips"],
            targeted_job_title=job_title,
            targeted_job_company=job_company,
            credits_used=5,
            last_analyzed_at=analysis_timestamp
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Resume analysis failed: {str(e)}")
