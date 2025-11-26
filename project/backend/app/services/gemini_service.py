"""
Google Gemini API Service
Job authenticity analysis using Google Gemini AI
Replaces Ruvia Trust API
"""

from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from app.core.config import settings
import google.generativeai as genai
import json
import re
import logging

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini API for job authenticity analysis"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.api_key = settings.GOOGLE_GEMINI_API_KEY
        
        if not self.api_key:
            raise ValueError("GOOGLE_GEMINI_API_KEY is not set in environment variables")
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        
        # First, get available models to find one that works
        available_models = self.list_available_models()
        
        if not available_models:
            raise ValueError(
                "No Gemini models available with generateContent support. "
                "Please check your API key and ensure Gemini API is enabled."
            )
        
        # Use specified model if provided, otherwise try common models in order
        models_to_try = []
        if model_name:
            models_to_try.append(model_name)
        
        # Add common model names (with and without 'models/' prefix)
        common_models = ['gemini-2.5-flash', 'gemini-2.5-pro']
        for common_model in common_models:
            if common_model not in models_to_try:
                models_to_try.append(common_model)
            # Also try with 'models/' prefix
            prefixed = f'models/{common_model}'
            if prefixed not in models_to_try:
                models_to_try.append(prefixed)
        
        # Try each model, checking if it's in available models
        model_initialized = False
        last_error = None
        
        for model_to_try in models_to_try:
            # Check if model is in available models list (handle both with and without 'models/' prefix)
            model_base = model_to_try.replace('models/', '')
            if model_base in available_models or model_to_try in available_models:
                try:
                    self.model = genai.GenerativeModel(model_to_try)
                    logger.info(f"Successfully initialized Gemini model: {model_to_try}")
                    model_initialized = True
                    break
                except Exception as e:
                    last_error = str(e)
                    logger.debug(f"Failed to initialize model '{model_to_try}': {str(e)}")
                    continue
        
        # If no model worked, try the first available model
        if not model_initialized and available_models:
            try:
                first_available = available_models[0]
                self.model = genai.GenerativeModel(first_available)
                logger.info(f"Using first available model: {first_available}")
                model_initialized = True
            except Exception as e:
                last_error = str(e)
        
        if not model_initialized:
            raise ValueError(
                f"Could not initialize any Gemini model. "
                f"Last error: {last_error}. "
                f"Available models: {', '.join(available_models)}"
            )
    
    def list_available_models(self) -> List[str]:
        """
        List all available Gemini models that support generateContent
        
        Returns:
            List of available model names (without 'models/' prefix)
        """
        try:
            models = genai.list_models()
            available_models = []
            for model in models:
                # Check if model supports generateContent
                if hasattr(model, 'supported_generation_methods'):
                    if 'generateContent' in model.supported_generation_methods:
                        # Remove 'models/' prefix if present
                        model_name = model.name.replace('models/', '')
                        available_models.append(model_name)
                        logger.debug(f"Found available model: {model_name}")
            
            logger.info(f"Found {len(available_models)} available models with generateContent: {available_models}")
            return available_models
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}", exc_info=True)
            # Return empty list so initialization can handle it
            return []
    
    async def analyze_job_authenticity(
        self,
        job_title: str,
        company: str,
        location: Optional[str],
        description: str
    ) -> Dict[str, Any]:
        """
        Analyze job posting for authenticity using Gemini API
        
        Args:
            job_title: Job title
            company: Company name
            location: Job location (optional)
            description: Job description
            
        Returns:
            Dict with keys:
                - is_authentic: bool (True if job is real, False if fake)
                - confidence_score: float (0-100 confidence in the assessment)
                - evidence: str (Reasoning and evidence for the decision)
        
        Raises:
            HTTPException: If API call fails
        """
        # Prepare the prompt for Gemini
        prompt = self._create_authenticity_prompt(job_title, company, location, description)
        
        try:
            # Call Gemini API (synchronous call, but method is async for consistency)
            # Wrap in executor if needed for non-blocking behavior
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            # Parse the response
            result = self._parse_gemini_response(response.text)

            logger.info(f"Gemini response: {response.text}")
            
            return result
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Gemini API error: {str(e)}"
            )
    
    def _create_authenticity_prompt(
        self,
        job_title: str,
        company: str,
        location: Optional[str],
        description: str
    ) -> str:
        """Create a detailed prompt for Gemini to analyze job authenticity"""
        
        location_text = f"Location: {location}\n" if location else ""
        
        prompt = f"""You are an expert job authenticity analyst. Analyze the following job posting and determine if it is a REAL job or a FAKE/scam job posting.

Additionally, extract the company name, location, and industry from the job description even if not explicitly provided.

Job Title: {job_title}
Company: {company}
{location_text}
Job Description:
{description}

## Few-Shot Examples for Data Extraction:

**Example 1:**
Description: "We're building for employer SMBs and their finance function, internal and external, and are focused on delivering a human-centric customer experience. Relay is the all-in-one, collaborative money management platform."
Extracted: company="Relay", industry="Finance/FinTech", location=null (not mentioned)

**Example 2:**
Description: "Join our team at Amazon Web Services in Seattle. We're looking for cloud engineers to build next-generation infrastructure."
Extracted: company="Amazon Web Services", industry="Cloud Computing/Technology", location="Seattle"

**Example 3:**
Description: "Tactable is a world-class cloud, data, and API engineering firm. Work from our downtown Toronto HQ in a hybrid environment."
Extracted: company="Tactable", industry="Software Engineering/Consulting", location="Toronto, ON"

## Your Task:

Analyze this job posting and provide your assessment in the following JSON format:
{{
    "is_authentic": true or false,
    "confidence_score": a number between 0 and 100,
    "evidence": "Your detailed reasoning explaining why you believe this job is real or fake. Include specific indicators, red flags, or positive signals you found. Use markdown formatting with headers, bullet points, and bold text for readability.",
    "extracted_data": {{
        "company": "The company name extracted or confirmed from the description",
        "location": "City, State/Province extracted from description (null if not found)",
        "industry": "Industry/sector extracted from description (null if not determinable)"
    }}
}}

Consider the following factors for authenticity:
1. Job description quality and detail
2. Company information and legitimacy
3. Job requirements and expectations
4. Language and communication style
5. Red flags (e.g., requests for payment, vague descriptions, suspicious contact methods)
6. Positive indicators (e.g., detailed requirements, professional language, clear company information)

IMPORTANT: 
- The "evidence" field should use markdown formatting (bold, lists, headers) for better readability.
- Always try to extract company, location, and industry from the description context.
- Provide your analysis in valid JSON format only, no additional text."""

        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini's response to extract structured data
        
        Args:
            response_text: Raw text response from Gemini
            
        Returns:
            Dict with is_authentic, confidence_score, evidence, extracted_data
        """
        # Default extracted_data structure
        default_extracted_data = {
            "company": None,
            "location": None,
            "industry": None
        }
        
        try:
            # Try to extract JSON from the response
            # Gemini might return JSON wrapped in markdown code blocks or plain text
            
            # Remove markdown code blocks if present (handle various formats)
            json_text = response_text.strip()
            
            # Remove ```json or ``` at the start
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            elif json_text.startswith('```'):
                json_text = json_text[3:]
            
            # Remove ``` at the end
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            
            json_text = json_text.strip()
            
            # Parse JSON directly - json.loads handles nested objects and escaped strings properly
            data = json.loads(json_text)
            
            # Extract and validate fields
            is_authentic = bool(data.get("is_authentic", False))
            confidence_score = float(data.get("confidence_score", 0.0))
            evidence = str(data.get("evidence", "No evidence provided"))
            
            # Extract the new extracted_data fields
            extracted_data = data.get("extracted_data", {})
            if not isinstance(extracted_data, dict):
                extracted_data = default_extracted_data
            else:
                # Ensure all fields exist and handle null values properly
                extracted_data = {
                    "company": extracted_data.get("company") if extracted_data.get("company") not in [None, "null", ""] else None,
                    "location": extracted_data.get("location") if extracted_data.get("location") not in [None, "null", ""] else None,
                    "industry": extracted_data.get("industry") if extracted_data.get("industry") not in [None, "null", ""] else None
                }
            
            # Ensure confidence_score is between 0 and 100
            confidence_score = max(0.0, min(100.0, confidence_score))
            
            logger.info(f"Successfully parsed Gemini response: is_authentic={is_authentic}, confidence={confidence_score}")
            
            return {
                "is_authentic": is_authentic,
                "confidence_score": confidence_score,
                "evidence": evidence,
                "extracted_data": extracted_data
            }
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse Gemini response as JSON: {str(e)}")
            logger.debug(f"Raw response (first 500 chars): {response_text[:500]}")
            
            # If parsing fails, try to extract information using regex
            # Fallback parsing
            is_authentic = False
            confidence_score = 50.0
            evidence = "Analysis completed but response parsing failed. Please try again."
            extracted_data = default_extracted_data
            
            # Try to find is_authentic in text
            authentic_match = re.search(r'"is_authentic"\s*:\s*(true|false)', response_text, re.IGNORECASE)
            if authentic_match:
                is_authentic = authentic_match.group(1).lower() == "true"
            
            # Try to find confidence_score
            confidence_match = re.search(r'"confidence_score"\s*:\s*(\d+\.?\d*)', response_text)
            if confidence_match:
                try:
                    confidence_score = float(confidence_match.group(1))
                    confidence_score = max(0.0, min(100.0, confidence_score))
                except ValueError:
                    pass
            
            # Try to extract evidence field using regex - it's a long string with escaped characters
            # Match "evidence": "..." where the content can span multiple lines and contain escaped chars
            evidence_match = re.search(r'"evidence"\s*:\s*"((?:[^"\\]|\\.)*)"', response_text, re.DOTALL)
            if evidence_match:
                # Decode escaped characters in the evidence string
                try:
                    evidence = evidence_match.group(1).encode().decode('unicode_escape')
                except Exception:
                    evidence = evidence_match.group(1).replace('\\n', '\n').replace('\\"', '"')
            
            # Try to extract extracted_data fields using regex
            company_match = re.search(r'"company"\s*:\s*"([^"]+)"', response_text)
            if company_match:
                extracted_data["company"] = company_match.group(1)
            
            location_match = re.search(r'"location"\s*:\s*"([^"]+)"', response_text)
            if location_match:
                extracted_data["location"] = location_match.group(1)
            
            industry_match = re.search(r'"industry"\s*:\s*"([^"]+)"', response_text)
            if industry_match:
                extracted_data["industry"] = industry_match.group(1)
            
            logger.info(f"Fallback parsing result: is_authentic={is_authentic}, confidence={confidence_score}")
            
            return {
                "is_authentic": is_authentic,
                "confidence_score": confidence_score,
                "evidence": evidence,
                "extracted_data": extracted_data
            }

