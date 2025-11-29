"""
Resume Analysis Service
Gemini AI-powered resume analysis for tips and match scoring
"""

import logging
import json
import re
from typing import Dict, Any, Optional
from app.services.gemini_service import GeminiService
from app.services.document_service import DocumentService
from app.logging_system import logger_manager as logger


class ResumeAnalysisService:
    """Service for analyzing resumes using Gemini AI"""
    
    def __init__(self):
        self.gemini_service = GeminiService()
        self.document_service = DocumentService()
    
    async def analyze_resume(
        self,
        resume_content: bytes,
        job_description: Optional[str] = None,
        job_title: Optional[str] = None,
        job_company: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a resume and generate tips and match score
        
        Args:
            resume_content: The resume file content as bytes
            job_description: Optional job description for targeted analysis
            job_title: Optional job title for context
            job_company: Optional company name for context
            
        Returns:
            Dict with 'tips' (str) and 'match_score' (float)
        """
        try:
            # Extract text from resume
            logger.info(f"Starting text extraction from resume content, size: {len(resume_content)} bytes")
            resume_text = self._extract_resume_text(resume_content)
            logger.info(f"Text extraction completed, extracted text length: {len(resume_text) if resume_text else 0}")

            if not resume_text or len(resume_text.strip()) < 100:
                logger.warning(f"Resume text extraction yielded insufficient content: '{resume_text[:200]}...'")
                return {
                    "tips": "Unable to extract sufficient text from the resume. Please ensure the file contains readable text.",
                    "match_score": 0.0
                }
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(
                resume_text=resume_text,
                job_description=job_description,
                job_title=job_title,
                job_company=job_company
            )
            
            # Call Gemini
            response = self.gemini_service.model.generate_content(prompt)
            
            if not response or not response.candidates:
                raise ValueError("Empty response from Gemini")
            
            # Handle multi-part responses by concatenating all text parts
            response_text = ""
            try:
                # Try simple text accessor first (for single-part responses)
                response_text = response.text
            except ValueError:
                # Multi-part response - concatenate all parts
                logger.info("Handling multi-part Gemini response")
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        response_text += part.text
            
            if not response_text.strip():
                raise ValueError("Empty text in Gemini response")
            
            # Parse response
            result = self._parse_analysis_response(response_text)
            
            logger.info(f"Resume analysis complete. Match score: {result['match_score']}")
            return result
            
        except Exception as e:
            logger.error(f"Resume analysis failed: {str(e)}", exc_info=True)
            return {
                "tips": f"Analysis failed: {str(e)}. Please try again later.",
                "match_score": 0.0
            }
    
    def _extract_resume_text(self, content: bytes) -> str:
        """Extract text from resume file (PDF or DOCX)"""
        try:
            logger.info(f"Starting text extraction for file of size {len(content)} bytes")

            # Try PDF extraction first
            try:
                logger.info("Attempting PDF extraction")
                text, metadata = self.document_service._extract_pdf_text(content)
                logger.info(f"PDF extraction result: {len(text)} characters, method: {metadata.get('extraction_method')}")
                if text and len(text.strip()) > 50:
                    logger.info("PDF extraction successful")
                    return text
                else:
                    logger.warning(f"PDF extraction yielded insufficient text: {len(text)} characters")
            except Exception as e:
                logger.warning(f"PDF extraction failed: {str(e)}")

            # Try DOCX extraction
            try:
                logger.info("Attempting DOCX extraction")
                text, metadata = self.document_service._extract_docx_text(content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                logger.info(f"DOCX extraction result: {len(text)} characters")
                if text and len(text.strip()) > 50:
                    logger.info("DOCX extraction successful")
                    return text
                else:
                    logger.warning(f"DOCX extraction yielded insufficient text: {len(text)} characters")
            except Exception as e:
                logger.warning(f"DOCX extraction failed: {str(e)}")

            # Try plain text extraction
            try:
                logger.info("Attempting plain text extraction")
                text, metadata = self.document_service._extract_plain_text(content)
                logger.info(f"Plain text extraction result: {len(text)} characters")
                if text and len(text.strip()) > 50:
                    logger.info("Plain text extraction successful")
                    return text
                else:
                    logger.warning(f"Plain text extraction yielded insufficient text: {len(text)} characters")
            except Exception as e:
                logger.warning(f"Plain text extraction failed: {str(e)}")

            # Fallback - try to decode as plain text
            logger.info("Attempting fallback text decoding")
            try:
                text = content.decode('utf-8')
                logger.info(f"UTF-8 decoding result: {len(text)} characters")
                if text and len(text.strip()) > 50:
                    return text
            except:
                try:
                    text = content.decode('latin-1', errors='ignore')
                    logger.info(f"Latin-1 decoding result: {len(text)} characters")
                    if text and len(text.strip()) > 50:
                        return text
                except:
                    pass

            logger.error("All text extraction methods failed")
            return ""

        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            return ""
    
    def _create_analysis_prompt(
        self,
        resume_text: str,
        job_description: Optional[str] = None,
        job_title: Optional[str] = None,
        job_company: Optional[str] = None
    ) -> str:
        """Create the prompt for Gemini analysis"""
        
        # Truncate resume text if too long (keep first 8000 chars)
        if len(resume_text) > 8000:
            resume_text = resume_text[:8000] + "\n...[truncated]..."
        
        if job_description:
            # Truncate job description if too long
            if len(job_description) > 3000:
                job_description = job_description[:3000] + "\n...[truncated]..."
            
            prompt = f"""You are an expert career coach and resume reviewer. Analyze the following resume against a specific job posting and provide actionable tips to improve the resume's match with the job.

## RESUME CONTENT:
{resume_text}

## TARGET JOB:
**Title:** {job_title or 'Not specified'}
**Company:** {job_company or 'Not specified'}

**Job Description:**
{job_description}

## ANALYSIS REQUIREMENTS:

Provide your analysis in the following JSON format ONLY:

{{
    "match_score": <number between 0-100>,
    "tips": "<markdown formatted tips>"
}}

### Match Score Guidelines:
- 90-100: Excellent match - resume strongly aligns with all key requirements
- 75-89: Good match - resume covers most requirements with minor gaps
- 60-74: Moderate match - resume has relevant experience but notable gaps
- 40-59: Partial match - some transferable skills but significant gaps
- 0-39: Low match - resume doesn't align well with job requirements

### Tips Format (Markdown):
Structure your tips as follows:

# Resume Analysis for {job_title or 'Target Position'}

## Overall Assessment
Brief 2-3 sentence summary of resume-job fit.

## Strengths
- Key strength 1
- Key strength 2
- Key strength 3

## Areas for Improvement

### 1. [Category Name]
Specific actionable advice...

### 2. [Category Name]
Specific actionable advice...

### 3. [Category Name]
Specific actionable advice...

## Keywords to Add
List specific keywords from the job description that should be incorporated.

## Quick Wins
3-5 immediate changes that would improve the match score.

---

Provide your response as valid JSON only. No additional text outside the JSON."""

        else:
            # General resume analysis without job context
            prompt = f"""You are an expert career coach and resume reviewer. Analyze the following resume and provide comprehensive tips to improve it for general job applications.

## RESUME CONTENT:
{resume_text}

## ANALYSIS REQUIREMENTS:

Provide your analysis in the following JSON format ONLY:

{{
    "match_score": <number between 0-100 representing overall resume quality>,
    "tips": "<markdown formatted tips>"
}}

### Quality Score Guidelines (when no specific job):
- 90-100: Exceptional resume - professional formatting, strong achievements, clear narrative
- 75-89: Strong resume - well-structured with good content, minor improvements possible
- 60-74: Good resume - solid foundation but needs refinement
- 40-59: Average resume - functional but lacks impact
- 0-39: Needs significant work - major improvements required

### Tips Format (Markdown):
Structure your tips as follows:

# Resume Analysis

## Overall Assessment
Brief 2-3 sentence summary of resume quality and potential.

## Strengths
- Key strength 1
- Key strength 2
- Key strength 3

## Areas for Improvement

### 1. Content & Achievements
Specific advice on improving bullet points, quantifying achievements, etc.

### 2. Format & Structure
Layout, organization, and visual presentation feedback.

### 3. Keywords & ATS Optimization
Tips for improving ATS compatibility.

### 4. Professional Summary
Feedback on summary/objective section.

## Industry-Specific Tips
Based on the apparent target industry, provide relevant advice.

## Quick Wins
3-5 immediate changes that would improve the resume.

---

Provide your response as valid JSON only. No additional text outside the JSON."""

        return prompt
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini's response into structured data with robust fallback"""
        try:
            cleaned = response_text.strip()
            logger.info(f"Parsing response, length: {len(cleaned)}, starts with: {cleaned[:100]}...")

            # 1. Aggressive Markdown Cleaning
            if "```" in cleaned:
                # Remove opening block
                if cleaned.startswith("```"):
                    first_newline = cleaned.find('\n')
                    if first_newline != -1:
                        cleaned = cleaned[first_newline + 1:].lstrip()
                    else:
                        cleaned = cleaned[3:].lstrip()
                
                # Remove closing block
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3].rstrip()

            logger.info(f"Cleaned response length: {len(cleaned)}")

            # 2. Primary Parsing: Try JSON loads on the whole text
            try:
                data = json.loads(cleaned)
                logger.info(f"Successfully parsed entire response as JSON")
                return self._validate_and_return(data)
            except json.JSONDecodeError:
                logger.info("Direct JSON parsing failed, trying extracting JSON substring...")

            # 3. Secondary Extraction: Find JSON boundaries
            start_idx = cleaned.find('{')
            end_idx = cleaned.rfind('}')

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_text = cleaned[start_idx:end_idx + 1]
                try:
                    data = json.loads(json_text)
                    logger.info(f"Successfully parsed JSON substring")
                    return self._validate_and_return(data)
                except json.JSONDecodeError:
                    logger.warning("JSON substring parsing failed, attempting manual extraction on substring...")
                    return self._manual_extraction(json_text)

            # 4. Aggressive Manual Extraction
            # If strict JSON boundaries check failed or didn't find valid JSON, 
            # but text contains key JSON fields, try manual extraction on the whole text.
            if '"match_score"' in cleaned or '"tips"' in cleaned:
                 logger.info("JSON parsing failed but found JSON keys, attempting manual extraction on full text...")
                 return self._manual_extraction(cleaned)

            # 5. Fallback: Check for Markdown content
            if "# Resume Analysis" in cleaned or "## Overall Assessment" in cleaned or "# Resume Analysis" in response_text:
                logger.info("Response appears to be raw markdown, using as tips")
                # If the original text looked like markdown but cleaning stripped too much, rely on original or cleaned
                tips_content = cleaned if "#" in cleaned else response_text
                return {
                    "match_score": 75.0, # Default since we can't find it
                    "tips": tips_content
                }

            logger.warning("All parsing attempts failed")
            return {
                "match_score": 50.0,
                "tips": cleaned
            }

        except Exception as e:
            logger.error(f"Error parsing analysis response: {str(e)}. Response: {response_text[:500]}...")
            return {
                "match_score": 0.0,
                "tips": f"Error parsing analysis: {str(e)}"
            }

    def _validate_and_return(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and format the parsed data"""
        match_score = float(data.get("match_score", 50))
        match_score = max(0, min(100, match_score))
        tips = str(data.get("tips", "No tips generated."))
        
        logger.info(f"Successfully parsed: match_score={match_score}, tips_length={len(tips)}")
        return {"match_score": match_score, "tips": tips}

    def _manual_extraction(self, text: str) -> Dict[str, Any]:
        """Manually extract fields when JSON parsing fails"""
        logger.info("Attempting character-by-character manual extraction")
        
        # Extract match_score
        match_score = 50.0
        score_match = re.search(r'"match_score"\s*:\s*(\d+(?:\.\d+)?)', text)
        if score_match:
            match_score = float(score_match.group(1))

        # Extract tips using character scanner
        tips = "No tips extracted."
        # Look for "tips": " or "tips" : " pattern
        tips_pattern = re.compile(r'"tips"\s*:\s*"')
        match = tips_pattern.search(text)
        
        if match:
            quote_start = match.end() - 1 # The opening quote index
            
            # Scan for closing quote
            current_pos = quote_start + 1
            found_closing = False
            
            while current_pos < len(text):
                if text[current_pos] == '"':
                    # Check backslashes to see if escaped
                    backslashes = 0
                    check_pos = current_pos - 1
                    while check_pos >= quote_start and text[check_pos] == '\\':
                        backslashes += 1
                        check_pos -= 1
                    
                    if backslashes % 2 == 0:
                        # It's a closing quote (even number of backslashes means they escape each other)
                        found_closing = True
                        raw_tips = text[quote_start + 1 : current_pos]
                        
                        # Attempt to unescape
                        try:
                            # Use json.loads on a wrapped string to handle all standard escapes
                            tips = json.loads(f'"{raw_tips}"')
                        except Exception:
                            # Manual unescape fallback
                            tips = raw_tips.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\').replace('\\t', '\t')
                        break
                current_pos += 1
            
            if not found_closing:
                logger.warning("Could not find closing quote for tips, taking valid substring")
                # If no closing quote found, take the rest of the string but warn
                tips = text[quote_start + 1:]
        
        return {"match_score": match_score, "tips": tips}


