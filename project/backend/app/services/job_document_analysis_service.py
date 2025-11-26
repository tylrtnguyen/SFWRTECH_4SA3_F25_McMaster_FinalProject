"""
Job Document Analysis Service
Analyzes uploaded job documents using Gemini AI
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

class JobDocumentAnalysisService:
    """Service for analyzing job documents using AI"""

    def __init__(self):
        self.gemini_service = GeminiService()

    async def analyze_job_document(
        self,
        document_text: str,
        filename: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze job document text using Gemini AI

        Args:
            document_text: Extracted text from the document
            filename: Original filename
            user_id: User who uploaded the document
            metadata: Additional document metadata

        Returns:
            Dict with analysis results including authenticity, extracted data, etc.
        """

        try:
            # Create enhanced analysis prompt
            prompt = self._create_document_analysis_prompt(document_text, filename, metadata or {})

            # Get Gemini analysis using the document-specific prompt
            logger.info(f"Analyzing document {filename} with Gemini AI using enhanced prompt")
            analysis_result = await self._analyze_with_gemini_direct(prompt, filename)

            # Enhance with document-specific analysis
            enhanced_analysis = self._enhance_document_analysis(
                document_text, analysis_result, filename, metadata or {}
            )

            logger.info(f"Document analysis completed for {filename}: authentic={enhanced_analysis.get('is_authentic')}, confidence={enhanced_analysis.get('confidence_score')}, scam_type={enhanced_analysis.get('scam_type', 'none')}")
            return enhanced_analysis

        except Exception as e:
            logger.error(f"Document analysis failed for {filename}: {str(e)}")
            return self._create_error_analysis(filename, str(e))

    async def _analyze_with_gemini_direct(self, prompt: str, filename: str) -> Dict[str, Any]:
        """Analyze document using Gemini directly with custom prompt"""
        try:
            import google.generativeai as genai

            # Configure Gemini
            genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)

            # Get available models and use the best one
            available_models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    available_models.append(model.name)

            # Prefer pro models, fallback to flash
            model_name = None
            for preferred in ['gemini-1.5-pro', 'gemini-1.0-pro', 'gemini-1.5-flash', 'gemini-pro']:
                if any(preferred in model for model in available_models):
                    model_name = next((m for m in available_models if preferred in m), None)
                    break

            if not model_name:
                model_name = available_models[0] if available_models else 'gemini-pro'

            model = genai.GenerativeModel(model_name)

            # Generate response
            response = await model.generate_content_async(prompt)
            response_text = response.text

            # Parse the JSON response
            return self._parse_document_analysis_response(response_text)

        except Exception as e:
            logger.error(f"Gemini direct analysis failed for {filename}: {str(e)}")
            return self._create_error_analysis(filename, f"Gemini analysis failed: {str(e)}")

    def _parse_document_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini's response for optimized document analysis"""
        try:
            # Extract JSON from response (handle markdown formatting)
            json_text = response_text.strip()

            # Remove markdown code blocks
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            elif json_text.startswith('```'):
                json_text = json_text[3:]

            if json_text.endswith('```'):
                json_text = json_text[:-3]

            json_text = json_text.strip()

            # Parse JSON
            data = json.loads(json_text)

            # Validate and structure the response
            result = {
                "is_authentic": bool(data.get("is_authentic", False)),
                "confidence_score": min(100, max(0, int(data.get("confidence_score", 0)))),
                "evidence": str(data.get("evidence", "Analysis completed")),
                "scam_type": str(data.get("scam_type", "none")),
                "extracted_data": data.get("extracted_data", {}),
                "risk_assessment": data.get("risk_assessment", {
                    "personal_data_risk": "low",
                    "financial_risk": "low",
                    "identity_risk": "low"
                }),
                "document_quality": {
                    "has_contact_info": bool(data.get("extracted_data", {}).get("contact_info", {}).get("emails", [])),
                    "has_requirements": bool(data.get("extracted_data", {}).get("requirements", [])),
                    "professional_language": len(data.get("extracted_data", {}).get("red_flags_found", [])) == 0,
                    "red_flags": data.get("extracted_data", {}).get("red_flags_found", [])
                }
            }

            return result

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse document analysis response: {str(e)}")
            # Return a safe default when parsing fails
            return {
                "is_authentic": False,
                "confidence_score": 25,
                "evidence": "Analysis encountered technical issues. Document flagged for manual review due to parsing errors.",
                "scam_type": "unknown",
                "extracted_data": {},
                "risk_assessment": {
                    "personal_data_risk": "medium",
                    "financial_risk": "low",
                    "identity_risk": "medium"
                },
                "document_quality": {
                    "has_contact_info": False,
                    "has_requirements": False,
                    "professional_language": False,
                    "red_flags": ["parsing_error"]
                }
            }

    def _create_document_analysis_prompt(self, text: str, filename: str, metadata: Dict[str, Any]) -> str:
        """Create specialized prompt for document analysis with enhanced scam detection"""
        doc_type = self._guess_document_type(filename)

        # Truncate content for token efficiency while keeping key sections
        content_preview = text[:1500] + ("..." if len(text) > 1500 else "")

        prompt = f"""Analyze this job document for scams. Filename: {filename}

CONTENT:
{content_preview}

RED FLAGS (mark fake if any present):
• Money handling/processing payments
• ID/personal documents required upfront
• Telegram/WhatsApp/Signal only communication
• Referral bonuses for recruiting others
• "No experience required" for technical roles
• Unrealistic salaries (>$150k entry-level, >$300k mid-level)
• Suspicious domains (.name, .xyz, .top, .club, .online, .site)
• Payment/fees required from candidate
• Overemphasis on remote work without office option
• Vague company info, no size/founding date/products

LEGITIMATE SIGNALS:
• Specific technical requirements
• Professional email domains (@company.com, @company.io, @company.net, @company.org)
• Realistic salary ranges
• Company details (size, founding, products)
• Standard hiring process mentioned

OUTPUT JSON:
{{
    "is_authentic": true/false,
    "confidence_score": 0-100,
    "evidence": "Brief explanation with specific red flags found",
    "scam_type": "money_mule|identity_theft|recruitment|fake_company|fees_required|other|none",
    "extracted_data": {{
        "title": "extracted job title",
        "company": "company name",
        "location": "location mentioned",
        "industry": "industry inferred",
        "salary_range": "salary info",
        "requirements": ["key requirements"],
        "contact_info": {{"emails": [], "websites": []}},
        "red_flags_found": ["list of red flags"]
    }},
    "risk_assessment": {{
        "personal_data_risk": "high|medium|low",
        "financial_risk": "high|medium|low",
        "identity_risk": "high|medium|low"
    }}
}}"""

        return prompt

    def _enhance_document_analysis(
        self,
        full_text: str,
        base_analysis: Dict[str, Any],
        filename: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance basic analysis with document-specific insights"""

        # Add document metadata
        base_analysis["document_metadata"] = {
            "filename": filename,
            "text_length": len(full_text),
            "word_count": len(full_text.split()),
            "document_type": self._guess_document_type(filename),
            "extraction_method": metadata.get("extraction_method", "unknown"),
            "analysis_status": "completed",
            **metadata
        }

        # Extract additional structured data if not already present
        extracted_data = base_analysis.get("extracted_data", {})

        # Enhance extracted data with additional parsing
        if not extracted_data.get("title"):
            extracted_data["title"] = self._extract_job_title(full_text)
        if not extracted_data.get("company"):
            extracted_data["company"] = self._extract_company(full_text)
        if not extracted_data.get("location"):
            extracted_data["location"] = self._extract_location(full_text)

        # Add contact information if not present
        if "contact_info" not in extracted_data:
            extracted_data["contact_info"] = self._extract_contact_info(full_text)

        # Add document quality assessment
        if "document_quality" not in base_analysis:
            base_analysis["document_quality"] = self._assess_document_quality(full_text)

        base_analysis["extracted_data"] = extracted_data
        return base_analysis

    def _guess_document_type(self, filename: str) -> str:
        """Guess document type from filename"""
        ext = filename.lower().split('.')[-1]
        types = {
            'pdf': 'PDF Document',
            'docx': 'Word Document (DOCX)',
            'doc': 'Word Document (DOC)',
            'txt': 'Plain Text File'
        }
        return types.get(ext, 'Unknown Document Type')

    def _extract_job_title(self, text: str) -> Optional[str]:
        """Extract job title from document text"""
        # Look for common job title patterns
        title_patterns = [
            r'(?:Job Title|Position|Role)[:\s]*([^\n\r]{1,100})',
            r'^([^\n\r]{1,50})(?:\n|\r|$)',  # First line might be title
            r'(?:We are hiring|Join us as)[:\s]*([^\n\r]{1,100})',
        ]

        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                title = match.group(1).strip()
                if len(title) > 3 and len(title) < 100:  # Reasonable title length
                    return title

        return None

    def _extract_company(self, text: str) -> Optional[str]:
        """Extract company name from document text"""
        company_patterns = [
            r'(?:Company|Organization|Employer)[:\s]*([^\n\r]{1,100})',
            r'(?:About|At) ([A-Z][A-Za-z\s&.,]{2,50})(?:\.|\n|$)',
            r'([A-Z][A-Za-z\s&.,]{2,50}) (?:is hiring|seeks|looking for)',
        ]

        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) > 2 and not any(word in company.lower() for word in ['the', 'and', 'for', 'with']):
                    return company

        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location information"""
        location_patterns = [
            r'(?:Location|Place|City|Address)[:\s]*([^\n\r]{1,100})',
            r'(?:based in|located in|work in) ([A-Z][A-Za-z\s,]{2,50})(?:\n|\.|\||$)',
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) > 2:
                    return location

        return None

    def _extract_contact_info(self, text: str) -> Dict[str, Any]:
        """Extract contact information"""
        # Email regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)

        # Phone regex (basic)
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        phones = re.findall(phone_pattern, text)

        return {
            "emails": emails[:3],  # Limit to first 3 emails
            "phones": [f"({p[0]}) {p[1]}-{p[2]}" for p in phones[:2]]  # Format and limit phones
        }

    def _assess_document_quality(self, text: str) -> Dict[str, Any]:
        """Assess the quality of the job document"""
        assessment = {
            "has_contact_info": False,
            "has_requirements": False,
            "has_benefits": False,
            "has_salary_info": False,
            "professional_language": True,
            "red_flags": []
        }

        # Check for contact information
        if re.search(r'@|\.com|\.org|\.net|phone|contact', text, re.IGNORECASE):
            assessment["has_contact_info"] = True

        # Check for requirements
        req_keywords = ['experience', 'skills', 'requirements', 'qualifications', 'must have']
        if any(keyword in text.lower() for keyword in req_keywords):
            assessment["has_requirements"] = True

        # Check for benefits
        benefit_keywords = ['benefits', 'salary', 'compensation', 'vacation', 'health', '401k', 'insurance']
        if any(keyword in text.lower() for keyword in benefit_keywords):
            assessment["has_benefits"] = True

        # Check for salary information
        salary_keywords = ['salary', 'pay', 'compensation', '\$', 'per hour', 'per year']
        if any(keyword in text.lower() for keyword in salary_keywords):
            assessment["has_salary_info"] = True

        # Check for red flags
        red_flag_patterns = [
            (r'\bpay.*first\b|\bfee.*required\b|\btraining.*cost\b', "Requests payment"),
            (r'\burgent\b|\bhurry\b|\blimited.*time\b', "Urgent language"),
            (r'\bwhatsapp\b|\btelegram\b|\bwire.*transfer\b', "Suspicious contact methods"),
            (r'\bgovernment.*grant\b|\bsecret.*job\b', "Unusual claims"),
        ]

        for pattern, flag in red_flag_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                assessment["red_flags"].append(flag)

        # Assess professional language (simple heuristic)
        if len(text.split()) < 50:  # Too short
            assessment["professional_language"] = False
        elif re.search(r'\b(?:lol|omg|wtf|damn|hell)\b', text, re.IGNORECASE):  # Informal language
            assessment["professional_language"] = False

        return assessment

    def _create_error_analysis(self, filename: str, error: str) -> Dict[str, Any]:
        """Create error analysis when processing fails"""
        return {
            "is_authentic": False,
            "confidence_score": 0.0,
            "evidence": f"Document analysis failed: {error}",
            "extracted_data": {
                "title": None,
                "company": None,
                "location": None,
                "industry": None
            },
            "document_metadata": {
                "filename": filename,
                "analysis_status": "failed",
                "error": error
            },
            "document_quality": {
                "has_contact_info": False,
                "has_requirements": False,
                "has_benefits": False,
                "has_salary_info": False,
                "professional_language": False,
                "red_flags": ["Analysis failed"]
            }
        }

