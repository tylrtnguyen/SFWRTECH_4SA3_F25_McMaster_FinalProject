"""
Google Cloud Storage Service
Handles file upload, deletion, and signed URL generation for resumes
"""

import os
import logging
from typing import Optional
from datetime import timedelta
from google.cloud import storage
from google.cloud.exceptions import NotFound
from app.core.config import settings

logger = logging.getLogger(__name__)


class GCSService:
    """Service for interacting with Google Cloud Storage"""

    _instance: Optional['GCSService'] = None
    _client: Optional[storage.Client] = None
    _bucket: Optional[storage.Bucket] = None

    def __init__(self):
        """Initialize GCS client and bucket (lazy initialization)"""
        # Don't initialize immediately - wait until first use
        pass
    
    @classmethod
    def get_instance(cls) -> 'GCSService':
        """Get singleton instance of GCSService"""
        if cls._instance is None:
            cls._instance = GCSService()
        return cls._instance

    def _ensure_initialized(self):
        """Ensure GCS client is initialized before use"""
        if self._client is None or self._bucket is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the GCS client and bucket"""
        try:
            # Set credentials path if provided
            if settings.GOOGLE_APPLICATION_CREDENTIALS:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.GOOGLE_APPLICATION_CREDENTIALS

            # Determine project ID - prefer GCS_PROJECT_ID, fallback to GOOGLE_PROJECT_ID
            project_id = settings.GOOGLE_PROJECT_ID
            bucket_name = settings.GOOGLE_GCS_BUCKET_NAME

            # Initialize client
            if project_id:
                self._client = storage.Client(project=project_id)
            else:
                self._client = storage.Client()

            # Get bucket
            if bucket_name:
                self._bucket = self._client.bucket(bucket_name)
                logger.info(f"GCS initialized with bucket: {bucket_name}")
            else:
                logger.warning("No GCS bucket name configured (checked GCS_BUCKET_NAME and GOOGLE_BUCKET_NAME) - GCS operations will fail")

        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {str(e)}")
            # Don't raise - allow app to start without GCS for development
            self._client = None
            self._bucket = None
    
    def is_configured(self) -> bool:
        """Check if GCS is properly configured"""
        self._ensure_initialized()
        return self._client is not None and self._bucket is not None
    
    def upload_file(self, file_content: bytes, object_id: str, content_type: str = "application/pdf") -> bool:
        """
        Upload a file to GCS

        Args:
            file_content: The file content as bytes
            object_id: The path/name for the file in the bucket
            content_type: MIME type of the file

        Returns:
            True if upload successful, False otherwise
        """
        self._ensure_initialized()
        if not self.is_configured():
            logger.warning("GCS not configured - skipping upload")
            return False
        
        try:
            blob = self._bucket.blob(object_id)
            blob.upload_from_string(file_content, content_type=content_type)
            logger.info(f"Successfully uploaded file to GCS: {object_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload file to GCS: {str(e)}")
            return False
    
    def delete_file(self, object_id: str) -> bool:
        """
        Delete a file from GCS

        Args:
            object_id: The path/name of the file in the bucket

        Returns:
            True if deletion successful or file doesn't exist, False on error
        """
        self._ensure_initialized()
        if not self.is_configured():
            logger.warning("GCS not configured - skipping delete")
            return False
        
        try:
            blob = self._bucket.blob(object_id)
            blob.delete()
            logger.info(f"Successfully deleted file from GCS: {object_id}")
            return True
        except NotFound:
            logger.warning(f"File not found in GCS (already deleted?): {object_id}")
            return True  # Consider this a success
        except Exception as e:
            logger.error(f"Failed to delete file from GCS: {str(e)}")
            return False
    
    def get_signed_url(self, object_id: str, expiration_minutes: int = 15) -> Optional[str]:
        """
        Generate a signed URL for temporary file access

        Args:
            object_id: The path/name of the file in the bucket
            expiration_minutes: How long the URL should be valid (default: 15 minutes)

        Returns:
            Signed URL string or None if generation fails
        """
        self._ensure_initialized()
        if not self.is_configured():
            logger.warning("GCS not configured - cannot generate signed URL")
            return None
        
        try:
            blob = self._bucket.blob(object_id)
            
            # Generate signed URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method="GET"
            )
            
            logger.debug(f"Generated signed URL for: {object_id}")
            return url
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {str(e)}")
            return None
    
    def get_download_url(self, object_id: str, expiration_minutes: int = 60) -> Optional[str]:
        """
        Generate a signed URL for file download with content-disposition header

        Args:
            object_id: The path/name of the file in the bucket
            expiration_minutes: How long the URL should be valid (default: 60 minutes)

        Returns:
            Signed URL string for download or None if generation fails
        """
        self._ensure_initialized()
        if not self.is_configured():
            logger.warning("GCS not configured - cannot generate download URL")
            return None
        
        try:
            blob = self._bucket.blob(object_id)
            
            # Extract filename from object_id
            filename = object_id.split("/")[-1] if "/" in object_id else object_id
            
            # Generate signed URL with download disposition
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method="GET",
                response_disposition=f'attachment; filename="{filename}"'
            )
            
            logger.debug(f"Generated download URL for: {object_id}")
            return url
        except Exception as e:
            logger.error(f"Failed to generate download URL: {str(e)}")
            return None
    
    def file_exists(self, object_id: str) -> bool:
        """
        Check if a file exists in GCS

        Args:
            object_id: The path/name of the file in the bucket

        Returns:
            True if file exists, False otherwise
        """
        self._ensure_initialized()
        if not self.is_configured():
            return False
        
        try:
            blob = self._bucket.blob(object_id)
            return blob.exists()
        except Exception as e:
            logger.error(f"Failed to check file existence: {str(e)}")
            return False
    
    def get_file_content(self, object_id: str) -> Optional[bytes]:
        """
        Download file content from GCS

        Args:
            object_id: The path/name of the file in the bucket

        Returns:
            File content as bytes or None if download fails
        """
        self._ensure_initialized()
        if not self.is_configured():
            logger.warning("GCS not configured - cannot download file")
            return None
        
        try:
            blob = self._bucket.blob(object_id)
            content = blob.download_as_bytes()
            logger.debug(f"Downloaded file from GCS: {object_id}")
            return content
        except NotFound:
            logger.warning(f"File not found in GCS: {object_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to download file from GCS: {str(e)}")
            return None

