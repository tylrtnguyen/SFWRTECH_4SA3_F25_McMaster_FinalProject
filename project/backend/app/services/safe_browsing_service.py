"""
Google Safe Browsing API Service
URL safety verification using Google Safe Browsing Lookup API v4
"""

from typing import Dict, Any 
from fastapi import HTTPException
from app.core.singleton import APIConnectionManager
from app.core.config import settings


class SafeBrowsingService:
    """Service for interacting with Google Safe Browsing Lookup API v4"""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_SAFE_BROWSING_API_KEY
        self.api_url = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
        
        if not self.api_key:
            raise ValueError("GOOGLE_SAFE_BROWSING_API_KEY is not set in environment variables")
    
    async def check_url_safety(self, url: str) -> Dict[str, Any]:
        """
        Check if a URL is safe using Google Safe Browsing Lookup API v4
        
        Args:
            url: The URL to check
            
        Returns:
            Dict with keys:
                - is_safe: bool (True if URL is safe, False if unsafe)
                - threat_types: List[str] (List of threat types if unsafe, empty if safe)
                - error: Optional[str] (Error message if API call failed)
        
        Raises:
            HTTPException: If URL is unsafe (is_safe=False)
        """
        api_manager = APIConnectionManager.get_instance()
        client = await api_manager.get_client()
        
        # Prepare request payload according to Safe Browsing API v4 spec
        payload = {
            "client": {
                "clientId": "jobtrust",
                "clientVersion": "1.0.0"
            },
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION"
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [
                    {"url": url}
                ]
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            # Make API request
            response = await client.post(
                f"{self.api_url}?key={self.api_key}",
                json=payload,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            
            result = response.json()
            
            # If matches field exists and is not empty, URL is unsafe
            if "matches" in result and result["matches"]:
                threat_types = [match.get("threatType", "UNKNOWN") for match in result["matches"]]
                
                # Raise exception to block unsafe URL
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Unsafe URL detected",
                        "is_safe": False,
                        "threat_types": threat_types,
                        "message": f"URL is flagged as unsafe by Google Safe Browsing. Threat types: {', '.join(threat_types)}"
                    }
                )
            
            # URL is safe
            return {
                "is_safe": True,
                "threat_types": [],
                "error": None
            }
            
        except HTTPException:
            # Re-raise HTTPException (unsafe URL)
            raise
        except Exception as e:
            # For API errors, log but don't block - allow URL through with warning
            # In production, you might want to be more strict
            return {
                "is_safe": True,  # Default to safe if API fails
                "threat_types": [],
                "error": f"Safe Browsing API error: {str(e)}"
            }


