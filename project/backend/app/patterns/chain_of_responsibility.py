"""
Chain of Responsibility Pattern
Modular job analysis pipelines for running detection, scoring, suggestions in order
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.models.schemas import JobAnalysisRequestInternal, JobAnalysisResult


class JobAnalysisHandler(ABC):
    """Abstract handler in the chain of responsibility"""
    
    def __init__(self):
        self._next_handler: Optional['JobAnalysisHandler'] = None
    
    def set_next(self, handler: 'JobAnalysisHandler') -> 'JobAnalysisHandler':
        """Set next handler in chain"""
        self._next_handler = handler
        return handler
    
    @abstractmethod
    async def handle(self, request: JobAnalysisRequestInternal, result: JobAnalysisResult) -> JobAnalysisResult:
        """Process the request and pass to next handler"""
        pass
    
    async def _handle_next(self, request: JobAnalysisRequestInternal, result: JobAnalysisResult) -> JobAnalysisResult:
        """Pass to next handler if exists"""
        if self._next_handler:
            return await self._next_handler.handle(request, result)
        return result


class FraudDetectionHandler(JobAnalysisHandler):
    """Handler for fraud detection using Gemini API (replaces Ruvia Trust)"""
    
    async def handle(self, request: JobAnalysisRequestInternal, result: JobAnalysisResult) -> JobAnalysisResult:
        """Detect fraud/authenticity in job posting using Gemini API"""
        from app.services.gemini_service import GeminiService
        
        try:
            gemini_service = GeminiService()
            authenticity_analysis = await gemini_service.analyze_job_authenticity(
                job_title=request.job_title,
                company=request.company_name,
                location=request.location,
                description=request.job_description
            )
            
            # Map Gemini results to JobAnalysisResult
            # is_authentic=True means job is real, so is_fraudulent=False
            result.is_fraudulent = not authenticity_analysis.get("is_authentic", False)
            
            # Map confidence_score (0-100) to fraud_score (0-1 scale)
            # Higher confidence that job is authentic = lower fraud score
            confidence_score = authenticity_analysis.get("confidence_score", 50.0)
            if result.is_fraudulent:
                # If fake, fraud_score = confidence_score / 100
                result.fraud_score = confidence_score / 100.0
            else:
                # If authentic, fraud_score = (100 - confidence_score) / 100
                result.fraud_score = (100.0 - confidence_score) / 100.0
            
            # Store evidence as fraud indicators
            evidence = authenticity_analysis.get("evidence", "")
            if evidence:
                result.fraud_indicators = [evidence]
            else:
                result.fraud_indicators = []
                
        except Exception as e:
            result.errors.append(f"Fraud detection error: {str(e)}")
        
        return await self._handle_next(request, result)


class JobScoringHandler(JobAnalysisHandler):
    """Handler for scoring job match quality"""
    
    async def handle(self, request: JobAnalysisRequestInternal, result: JobAnalysisResult) -> JobAnalysisResult:
        """Score job match quality"""
        try:
            # Calculate match score based on various factors
            score = 0.0
            factors = []
            
            # Factor 1: Job description completeness
            if request.job_description and len(request.job_description) > 100:
                score += 0.2
                factors.append("Complete job description")
            
            # Factor 2: Company information
            if request.company_name:
                score += 0.2
                factors.append("Company information provided")
            
            # Factor 3: Location information
            if request.location:
                score += 0.2
                factors.append("Location specified")
            
            # Factor 4: Salary information
            if request.salary_min or request.salary_max:
                score += 0.2
                factors.append("Salary information available")
            
            # Factor 5: Requirements clarity
            if request.requirements and len(request.requirements) > 50:
                score += 0.2
                factors.append("Clear requirements")
            
            result.match_score = min(score, 1.0)
            result.scoring_factors = factors
        except Exception as e:
            result.errors.append(f"Scoring error: {str(e)}")
        
        return await self._handle_next(request, result)


class SuggestionHandler(JobAnalysisHandler):
    """Handler for generating job suggestions"""
    
    async def handle(self, request: JobAnalysisRequestInternal, result: JobAnalysisResult) -> JobAnalysisResult:
        """Generate suggestions for job posting"""
        try:
            suggestions = []
            
            # Suggestion based on fraud score
            if result.fraud_score and result.fraud_score > 0.7:
                suggestions.append("High fraud risk detected. Verify company credentials.")
            elif result.is_fraudulent:
                suggestions.append("Job authenticity verification failed. Exercise caution.")
            
            # Suggestion based on match score
            if result.match_score and result.match_score < 0.5:
                suggestions.append("Job posting lacks important details. Request more information.")
            
            # Suggestion based on missing information
            if not request.salary_min and not request.salary_max:
                suggestions.append("Consider requesting salary range information.")
            
            if not request.location:
                suggestions.append("Location information would improve job match quality.")
            
            result.suggestions = suggestions
        except Exception as e:
            result.errors.append(f"Suggestion generation error: {str(e)}")
        
        return await self._handle_next(request, result)


class JobAnalysisPipeline:
    """Pipeline that orchestrates the chain of responsibility"""
    
    def __init__(self):
        self.handlers = []
    
    def add_handler(self, handler: JobAnalysisHandler):
        """Add handler to pipeline"""
        self.handlers.append(handler)
        return self
    
    def build_chain(self) -> Optional[JobAnalysisHandler]:
        """Build the chain of handlers"""
        if not self.handlers:
            return None
        
        # Set up chain
        for i in range(len(self.handlers) - 1):
            self.handlers[i].set_next(self.handlers[i + 1])
        
        return self.handlers[0]
    
    async def process(self, request: JobAnalysisRequestInternal) -> JobAnalysisResult:
        """Process request through the chain"""
        from app.models.schemas import JobAnalysisResult
        
        result = JobAnalysisResult()
        first_handler = self.build_chain()
        
        if first_handler:
            result = await first_handler.handle(request, result)
        
        return result

