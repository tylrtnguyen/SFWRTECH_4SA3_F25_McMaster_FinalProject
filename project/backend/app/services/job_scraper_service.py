"""
Job Scraper Service
Web scraping for job postings from various platforms (LinkedIn, Indeed, etc.)
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException
from bs4 import BeautifulSoup
import json
import re
from app.core.singleton import APIConnectionManager
import logging

logger = logging.getLogger(__name__)

class JobScraperService:
    """Service for scraping job postings from various platforms"""
    
    def __init__(self):
        self.api_manager = APIConnectionManager.get_instance()
    
    async def scrape_linkedin_job(self, url: str) -> Dict[str, Any]:
        """
        Scrape job data from LinkedIn job posting URL
        
        Args:
            url: LinkedIn job posting URL (e.g., https://www.linkedin.com/jobs/view/...)
            
        Returns:
            Dict with keys: title, company, location, industry (optional), source, source_url, description
            
        Raises:
            HTTPException: If scraping fails or URL is invalid
        """
        # Validate LinkedIn URL format
        if not self._is_linkedin_url(url):
            raise HTTPException(
                status_code=400,
                detail="Invalid LinkedIn URL format. Expected format: https://www.linkedin.com/jobs/view/..."
            )
        
        client = await self.api_manager.get_client()
        
        # Set headers to mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        try:
            # Fetch the page
            response = await client.get(url, headers=headers, timeout=30.0, follow_redirects=True)
            response.raise_for_status()
            
            html_content = response.text
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            
            # LinkedIn embeds job data in JSON-LD script tags or in window.__INITIAL_STATE__
            # Try to find JSON-LD data first
            job_data = self._extract_linkedin_json_data(soup, html_content)
            
            # Log extracted job data for debugging (use info level so it's visible)
            logger.info(f"Extracted job data from LinkedIn page: {job_data}")
            logger.debug(f"Full job_data dict: {json.dumps(job_data, indent=2, default=str)}")
            
            if not job_data:
                logger.error("No job data extracted from LinkedIn page")
                raise HTTPException(
                    status_code=500,
                    detail="Could not extract job data from LinkedIn page. The page structure may have changed."
                )
            
            # Extract fields from the parsed data
            title = job_data.get("title", "")
            company = job_data.get("company", "")
            location = job_data.get("location")
            industry = job_data.get("industry")
            description = job_data.get("description", "")
            
            # Log what fields were extracted
            logger.info(f"Extracted fields - title: '{title}', company: '{company}', location: '{location}'")
            
            # Validate required fields
            if not title or not company:
                missing_fields = []
                if not title:
                    missing_fields.append("title")
                if not company:
                    missing_fields.append("company")
                logger.error(f"Missing required fields: {missing_fields}. Full job_data: {json.dumps(job_data, indent=2, default=str)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Could not extract required job fields ({', '.join(missing_fields)}) from LinkedIn page. Extracted data: {job_data}"
                )
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "industry": industry,
                "source": "linkedin",
                "source_url": url,
                "description": description
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to scrape LinkedIn job: {str(e)}"
            )
    
    def _is_linkedin_url(self, url: str) -> bool:
        """Check if URL is a valid LinkedIn job URL"""
        pattern = r'^https?://(www\.)?linkedin\.com/jobs/view/'
        return bool(re.match(pattern, url))
    
    def _extract_linkedin_json_data(self, soup: BeautifulSoup, html_content: str) -> Optional[Dict[str, Any]]:
        """
        Extract job data from LinkedIn page
        LinkedIn embeds data in multiple places:
        1. JSON-LD script tags
        2. window.__INITIAL_STATE__ or similar JavaScript variables
        3. Inline JSON in script tags
        """
        job_data = {}
        
        # Method 1: Try to find JSON-LD script tags
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Look for jobPosting schema
                    if data.get("@type") == "JobPosting" or "JobPosting" in str(data):
                        job_data.update(self._parse_job_posting_schema(data))
            except (json.JSONDecodeError, AttributeError):
                continue
        
        # Method 2: Try to extract from window.__INITIAL_STATE__ or similar
        # LinkedIn often embeds data in JavaScript variables
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string:
                # Look for job posting data in JavaScript
                # Pattern: "jobsDashJobPostingsById" or similar
                content = script.string
                
                # Try to find JSON data embedded in script
                # Look for patterns like: {"data":{"*jobsDashJobPostingsById":...
                json_match = re.search(r'jobsDashJobPostingsById["\']?\s*:\s*({[^}]+})', content)
                if json_match:
                    try:
                        # Try to extract more complete JSON
                        # LinkedIn uses complex nested structures
                        # Look for the full job posting object
                        job_match = re.search(
                            r'jobsDashJobPostingsById["\']?\s*:\s*({.*?"title".*?"company".*?})',
                            content,
                            re.DOTALL
                        )
                        if job_match:
                            # This is a simplified extraction - LinkedIn's actual structure is complex
                            pass
                    except Exception:
                        pass
                
                # Look for window.__INITIAL_STATE__ or similar
                state_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', content, re.DOTALL)
                if state_match:
                    try:
                        state_data = json.loads(state_match.group(1))
                        # Navigate through LinkedIn's nested structure
                        # This is a simplified version - actual structure may vary
                        if "data" in state_data:
                            job_data.update(self._extract_from_nested_data(state_data["data"]))
                    except (json.JSONDecodeError, KeyError):
                        pass
        
        # Method 3: Try to extract from meta tags or other HTML elements
        if not job_data.get("title"):
            # Try to get title from page title or h1
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                job_data["title"] = title_tag.get_text(strip=True)
                logger.debug(f"Extracted title from HTML tag: {job_data['title']}")
        
        if not job_data.get("company"):
            # Try to find company name in various places
            # LinkedIn uses various selectors for company name
            company_selectors = [
                {'data-tracking-control-name': re.compile('company')},
                {'class': re.compile('job-details-jobs-unified-top-card__company-name|topcard__org-name-link')},
                {'data-test-id': 'job-poster-name'}
            ]
            for selector in company_selectors:
                company_tag = soup.find('a', selector) or soup.find('span', selector)
                if company_tag:
                    job_data["company"] = company_tag.get_text(strip=True)
                    logger.debug(f"Extracted company from HTML tag: {job_data['company']}")
                    break
        
        if not job_data.get("description"):
            # Try to find description
            desc_selectors = [
                {'class': re.compile('description|job-details|show-more-less-html__markup')},
                {'id': re.compile('job-details')},
                {'data-test-id': 'job-details'}
            ]
            for selector in desc_selectors:
                desc_tag = soup.find('div', selector)
                if desc_tag:
                    job_data["description"] = desc_tag.get_text(strip=True)
                    logger.debug(f"Extracted description (length: {len(job_data['description'])})")
                    break
        
        logger.debug(f"Final extracted job_data keys: {list(job_data.keys())}")
        return job_data if job_data else None
    
    def _parse_job_posting_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JSON-LD JobPosting schema"""
        result = {}
        
        if "title" in data:
            result["title"] = data["title"]
        if "hiringOrganization" in data:
            org = data["hiringOrganization"]
            if isinstance(org, dict):
                result["company"] = org.get("name", "")
            else:
                result["company"] = str(org)
        if "jobLocation" in data:
            location = data["jobLocation"]
            if isinstance(location, dict):
                if "address" in location:
                    addr = location["address"]
                    if isinstance(addr, dict):
                        parts = []
                        if "addressLocality" in addr:
                            parts.append(addr["addressLocality"])
                        if "addressRegion" in addr:
                            parts.append(addr["addressRegion"])
                        result["location"] = ", ".join(parts)
        if "description" in data:
            result["description"] = data["description"]
        if "industry" in data:
            result["industry"] = data["industry"]
        
        return result
    
    def _extract_from_nested_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract job data from LinkedIn's nested JSON structure"""
        result = {}
        
        # Navigate through LinkedIn's complex nested structure
        # Based on the user's example, data is nested like:
        # data -> data -> jobsDashJobPostingsById -> ...
        
        def find_job_posting(obj, path=""):
            """Recursively search for job posting data"""
            if isinstance(obj, dict):
                # Look for common LinkedIn job fields
                if "title" in obj and "company" in obj:
                    return obj
                
                # Look for job posting indicators
                if "jobsDashJobPostingsById" in obj:
                    posting_data = obj["jobsDashJobPostingsById"]
                    if isinstance(posting_data, dict):
                        return posting_data
                
                # Recursively search nested objects
                for key, value in obj.items():
                    result = find_job_posting(value, f"{path}.{key}")
                    if result:
                        return result
            
            elif isinstance(obj, list):
                for item in obj:
                    result = find_job_posting(item, path)
                    if result:
                        return result
            
            return None
        
        job_posting = find_job_posting(data)
        
        if job_posting:
            if "title" in job_posting:
                result["title"] = job_posting["title"]
            if "companyDetails" in job_posting:
                company_details = job_posting["companyDetails"]
                if isinstance(company_details, dict) and "name" in company_details:
                    result["company"] = company_details["name"]
            if "location" in job_posting:
                location = job_posting["location"]
                if isinstance(location, dict):
                    result["location"] = location.get("defaultLocalizedName") or location.get("abbreviatedLocalizedName", "")
                else:
                    result["location"] = str(location)
            if "description" in job_posting:
                desc = job_posting["description"]
                if isinstance(desc, dict) and "text" in desc:
                    result["description"] = desc["text"]
                else:
                    result["description"] = str(desc)
            if "industryV2Taxonomy" in job_posting:
                industry = job_posting["industryV2Taxonomy"]
                if isinstance(industry, list) and len(industry) > 0:
                    if isinstance(industry[0], dict) and "name" in industry[0]:
                        result["industry"] = industry[0]["name"]
        
        return result

