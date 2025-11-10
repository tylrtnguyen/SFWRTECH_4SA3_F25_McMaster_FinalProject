"""
Ruvia Trust API Service
Job fraud analysis integration
"""

from typing import Dict, Any
from app.core.singleton import APIConnectionManager
from app.core.config import settings


class RuviaTrustService:
    """Service for interacting with Ruvia Trust API"""
    
    def __init__(self):
        self.api_key = settings.RUVIA_TRUST_API_KEY
        self.api_url = settings.RUVIA_TRUST_API_URL
    
    async def analyze_job_fraud(
        self,
        job_title: str,
        company_name: str,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Analyze job posting for fraud indicators
        
        Args:
            job_title: Job title
            company_name: Company name
            job_description: Job description
            
        Returns:
            Fraud analysis results
        """
        api_manager = APIConnectionManager.get_instance()
        client = await api_manager.get_client()
        
        # Prepare request payload
        payload = {
            "job_title": job_title,
            "company_name": company_name,
            "job_description": job_description
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # Make API request
            response = await client.post(
                f"{self.api_url}/analyze",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # Fallback to mock analysis if API is unavailable
            return self._mock_fraud_analysis(job_title, company_name, job_description)
    
    def _mock_fraud_analysis(
        self,
        job_title: str,
        company_name: str,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Mock fraud analysis (used when API is unavailable)
        In production, this would be removed or only used for testing
        """
        # Simple heuristic-based fraud detection
        fraud_indicators = []
        fraud_score = 0.0
        
        # Check for common fraud indicators
        description_lower = job_description.lower()
        title_lower = job_title.lower()
        
        # Indicator 1: Suspicious keywords
        suspicious_keywords = ["work from home", "make money fast", "no experience needed"]
        if any(keyword in description_lower for keyword in suspicious_keywords):
            fraud_score += 0.3
            fraud_indicators.append("Contains suspicious keywords")
        
        # Indicator 2: Very short description
        if len(job_description) < 100:
            fraud_score += 0.2
            fraud_indicators.append("Job description too short")
        
        # Indicator 3: Missing company information
        if not company_name or len(company_name) < 2:
            fraud_score += 0.3
            fraud_indicators.append("Missing or invalid company name")
        
        # Indicator 4: Excessive use of caps
        if sum(1 for c in job_description if c.isupper()) > len(job_description) * 0.3:
            fraud_score += 0.2
            fraud_indicators.append("Excessive use of capital letters")
        
        return {
            "fraud_score": min(fraud_score, 1.0),
            "is_fraudulent": fraud_score > 0.6,
            "indicators": fraud_indicators,
            "confidence": 0.85 if fraud_score > 0.6 else 0.5
        }

