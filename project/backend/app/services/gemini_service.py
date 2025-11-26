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

Job Title: {job_title}
Company: {company}
{location_text}
Job Description:
{description}

Please analyze this job posting and provide your assessment in the following JSON format:
{{
    "is_authentic": true or false,
    "confidence_score": a number between 0 and 100,
    "evidence": "Your detailed reasoning explaining why you believe this job is real or fake. Include specific indicators, red flags, or positive signals you found."
}}

Consider the following factors:
1. Job description quality and detail
2. Company information and legitimacy
3. Job requirements and expectations
4. Language and communication style
5. Red flags (e.g., requests for payment, vague descriptions, suspicious contact methods)
6. Positive indicators (e.g., detailed requirements, professional language, clear company information)

Provide your analysis in valid JSON format only, no additional text."""

        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini's response to extract structured data
        
        Args:
            response_text: Raw text response from Gemini
            
        Returns:
            Dict with is_authentic, confidence_score, evidence
        """
        try:
            # Try to extract JSON from the response
            # Gemini might return JSON wrapped in markdown code blocks or plain text
            
            # Remove markdown code blocks if present
            json_text = re.sub(r'```json\s*', '', response_text)
            json_text = re.sub(r'```\s*', '', json_text)
            json_text = json_text.strip()
            
            # Try to find JSON object in the text
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', json_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
            
            # Parse JSON
            data = json.loads(json_text)
            
            # Extract and validate fields
            is_authentic = bool(data.get("is_authentic", False))
            confidence_score = float(data.get("confidence_score", 0.0))
            evidence = str(data.get("evidence", "No evidence provided"))
            
            # Ensure confidence_score is between 0 and 100
            confidence_score = max(0.0, min(100.0, confidence_score))
            
            return {
                "is_authentic": is_authentic,
                "confidence_score": confidence_score,
                "evidence": evidence
            }
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # If parsing fails, try to extract information using regex
            # Fallback parsing
            is_authentic = False
            confidence_score = 50.0
            evidence = response_text
            
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
            
            return {
                "is_authentic": is_authentic,
                "confidence_score": confidence_score,
                "evidence": evidence
            }

