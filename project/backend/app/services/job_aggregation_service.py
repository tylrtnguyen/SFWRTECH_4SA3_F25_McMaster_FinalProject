"""
Job Aggregation Service
Fetches jobs from LinkedIn and Indeed feeds
"""

from typing import List, Dict, Any, Optional
from app.core.singleton import APIConnectionManager
from app.core.config import settings
from app.models.schemas import Job


class JobAggregationService:
    """Service for aggregating jobs from multiple sources"""
    
    def __init__(self):
        self.linkedin_api_key = settings.LINKEDIN_API_KEY
        self.linkedin_api_url = settings.LINKEDIN_API_URL
        self.indeed_api_key = settings.INDEED_API_KEY
        self.indeed_api_url = settings.INDEED_API_URL
    
    async def fetch_linkedin_jobs(
        self,
        keywords: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 10
    ) -> List[Job]:
        """
        Fetch jobs from LinkedIn API
        
        Args:
            keywords: Search keywords
            location: Location filter
            limit: Maximum number of jobs to return
            
        Returns:
            List of Job objects
        """
        api_manager = APIConnectionManager.get_instance()
        client = await api_manager.get_client()
        
        headers = {
            "Authorization": f"Bearer {self.linkedin_api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "keywords": keywords or "",
            "location": location or "",
            "count": limit
        }
        
        try:
            response = await client.get(
                f"{self.linkedin_api_url}/jobSearch",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # Transform LinkedIn response to Job objects
            jobs = []
            for item in data.get("elements", [])[:limit]:
                job = Job(
                    id=f"linkedin_{item.get('id', '')}",
                    title=item.get("title", ""),
                    company_name=item.get("companyName", ""),
                    location=item.get("location", {}).get("name", ""),
                    job_description=item.get("description", {}).get("text", ""),
                    salary_min=item.get("salaryRange", {}).get("start", {}).get("amount"),
                    salary_max=item.get("salaryRange", {}).get("end", {}).get("amount"),
                    required_skills=item.get("skills", []),
                    job_url=item.get("jobPostingUrl", ""),
                    source="linkedin"
                )
                jobs.append(job)
            
            return jobs
        except Exception as e:
            # Fallback to mock data if API is unavailable
            return self._mock_linkedin_jobs(keywords, location, limit)
    
    async def fetch_indeed_jobs(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 10
    ) -> List[Job]:
        """
        Fetch jobs from Indeed API
        
        Args:
            query: Search query
            location: Location filter
            limit: Maximum number of jobs to return
            
        Returns:
            List of Job objects
        """
        api_manager = APIConnectionManager.get_instance()
        client = await api_manager.get_client()
        
        params = {
            "publisher": self.indeed_api_key,
            "q": query or "",
            "l": location or "",
            "limit": limit,
            "format": "json"
        }
        
        try:
            response = await client.get(
                self.indeed_api_url,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # Transform Indeed response to Job objects
            jobs = []
            for item in data.get("results", [])[:limit]:
                job = Job(
                    id=f"indeed_{item.get('jobkey', '')}",
                    title=item.get("jobtitle", ""),
                    company_name=item.get("company", ""),
                    location=item.get("formattedLocation", ""),
                    job_description=item.get("snippet", ""),
                    salary_min=None,  # Indeed API may not provide salary in free tier
                    salary_max=None,
                    required_skills=[],
                    job_url=item.get("url", ""),
                    source="indeed"
                )
                jobs.append(job)
            
            return jobs
        except Exception as e:
            # Fallback to mock data if API is unavailable
            return self._mock_indeed_jobs(query, location, limit)
    
    async def aggregate_jobs(
        self,
        keywords: Optional[str] = None,
        location: Optional[str] = None,
        sources: List[str] = None,
        limit: int = 20
    ) -> List[Job]:
        """
        Aggregate jobs from multiple sources
        
        Args:
            keywords: Search keywords
            location: Location filter
            sources: List of sources to fetch from (linkedin, indeed)
            limit: Maximum number of jobs per source
            
        Returns:
            Combined list of Job objects
        """
        if sources is None:
            sources = ["linkedin", "indeed"]
        
        all_jobs = []
        
        if "linkedin" in sources:
            linkedin_jobs = await self.fetch_linkedin_jobs(keywords, location, limit)
            all_jobs.extend(linkedin_jobs)
        
        if "indeed" in sources:
            indeed_jobs = await self.fetch_indeed_jobs(keywords, location, limit)
            all_jobs.extend(indeed_jobs)
        
        # Remove duplicates based on job title and company
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = (job.title.lower(), job.company_name.lower())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _mock_linkedin_jobs(
        self,
        keywords: Optional[str],
        location: Optional[str],
        limit: int
    ) -> List[Job]:
        """Mock LinkedIn jobs for testing"""
        return [
            Job(
                id="linkedin_mock_1",
                title="Software Engineer",
                company_name="Tech Corp",
                location=location or "San Francisco, CA",
                job_description="We are looking for a skilled software engineer...",
                salary_min=100000,
                salary_max=150000,
                required_skills=["Python", "FastAPI", "Docker"],
                job_url="https://linkedin.com/jobs/view/123",
                source="linkedin"
            )
        ]
    
    def _mock_indeed_jobs(
        self,
        query: Optional[str],
        location: Optional[str],
        limit: int
    ) -> List[Job]:
        """Mock Indeed jobs for testing"""
        return [
            Job(
                id="indeed_mock_1",
                title="Senior Developer",
                company_name="Dev Solutions",
                location=location or "Remote",
                job_description="Join our team as a senior developer...",
                salary_min=120000,
                salary_max=180000,
                required_skills=["Python", "React", "AWS"],
                job_url="https://indeed.com/viewjob?jk=456",
                source="indeed"
            )
        ]

