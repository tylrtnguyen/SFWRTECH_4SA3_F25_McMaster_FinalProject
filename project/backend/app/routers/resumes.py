"""
Resumes Router
Handles resume CRUD operations and file management
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from uuid import UUID
from uuid import uuid4
from datetime import datetime, timezone
from typing import List, Optional
from app.models.schemas import (
    ResumeCreate,
    ResumeResponse,
    Resume
)
from app.core.singleton import DatabaseManager

router = APIRouter()


def get_current_user_id() -> UUID:
    """
    Dependency to get current user ID from authentication
    This is a placeholder - integrate with your auth system
    """
    # TODO: Implement actual authentication
    raise NotImplementedError("Authentication not implemented")


@router.post("/", response_model=ResumeResponse)
async def create_resume(
    file: UploadFile = File(...),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Upload a new resume file
    
    This endpoint handles:
    1. File upload to GCP Cloud Storage
    2. Database record creation
    3. Returns resume metadata
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # TODO: Upload to GCP Cloud Storage and get object_id
        # For now, generate a placeholder object_id
        object_id = f"resumes/{user_id}/{uuid4()}/{file.filename}"
        
        # Create resume record in database
        resume_id = uuid4()
        uploaded_date = datetime.now(timezone.utc)
        
        resume_data = {
            "id": str(resume_id),
            "filename": file.filename,
            "size": file_size,
            "uploaded_date": uploaded_date.isoformat(),
            "object_id": object_id,
            "user_id": str(user_id),
            "last_match_job_bookmark_id": None,
            "recommended_tips": None
        }
        
        result = supabase.table("resumes").insert(resume_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create resume record")
        
        return ResumeResponse(
            id=resume_id,
            filename=file.filename,
            size=file_size,
            uploaded_date=uploaded_date,
            object_id=object_id,
            user_id=user_id,
            last_match_job_bookmark_id=None,
            recommended_tips=None
        )
    except HTTPException:
        raise
    except Exception as e:
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
        
        response = supabase.table("resumes").select(
            "id, filename, size, uploaded_date, object_id, user_id, last_match_job_bookmark_id, recommended_tips"
        ).eq("user_id", str(user_id)).order("uploaded_date", desc=True).execute()
        
        resumes = []
        for row in response.data:
            resumes.append(ResumeResponse(
                id=UUID(row["id"]),
                filename=row["filename"],
                size=row["size"],
                uploaded_date=datetime.fromisoformat(row["uploaded_date"].replace("Z", "+00:00")),
                object_id=row["object_id"],
                user_id=UUID(row["user_id"]),
                last_match_job_bookmark_id=UUID(row["last_match_job_bookmark_id"]) if row["last_match_job_bookmark_id"] else None,
                recommended_tips=row["recommended_tips"]
            ))
        
        return resumes
    except Exception as e:
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
        
        response = supabase.table("resumes").select(
            "id, filename, size, uploaded_date, object_id, user_id, last_match_job_bookmark_id, recommended_tips"
        ).eq("id", str(resume_id)).eq("user_id", str(user_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        row = response.data[0]
        return ResumeResponse(
            id=UUID(row["id"]),
            filename=row["filename"],
            size=row["size"],
            uploaded_date=datetime.fromisoformat(row["uploaded_date"].replace("Z", "+00:00")),
            object_id=row["object_id"],
            user_id=UUID(row["user_id"]),
            last_match_job_bookmark_id=UUID(row["last_match_job_bookmark_id"]) if row["last_match_job_bookmark_id"] else None,
            recommended_tips=row["recommended_tips"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resume: {str(e)}")


@router.put("/{resume_id}/tips")
async def update_resume_tips(
    resume_id: UUID,
    recommended_tips: str,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Update recommended tips for a resume
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        # Verify resume belongs to user
        check_response = supabase.table("resumes").select("id").eq("id", str(resume_id)).eq("user_id", str(user_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Update tips
        result = supabase.table("resumes").update({
            "recommended_tips": recommended_tips
        }).eq("id", str(resume_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update resume tips")
        
        return {"success": True, "message": "Resume tips updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update resume tips: {str(e)}")


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Delete a resume
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        # Verify resume belongs to user
        check_response = supabase.table("resumes").select("id, object_id").eq("id", str(resume_id)).eq("user_id", str(user_id)).execute()
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # TODO: Delete file from GCP Cloud Storage using object_id
        object_id = check_response.data[0]["object_id"]
        
        # Delete database record
        result = supabase.table("resumes").delete().eq("id", str(resume_id)).execute()
        
        return {"success": True, "message": "Resume deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete resume: {str(e)}")

