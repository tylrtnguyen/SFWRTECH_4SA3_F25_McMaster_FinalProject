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
    """Handler for fraud detection using Ruvia Trust API"""
    
    async def handle(self, request: JobAnalysisRequestInternal, result: JobAnalysisResult) -> JobAnalysisResult:
        """Detect fraud in job posting"""
        from app.services.ruvia_service import RuviaTrustService
        
        try:
            ruvia_service = RuviaTrustService()
            fraud_analysis = await ruvia_service.analyze_job_fraud(
                job_title=request.job_title,
                company_name=request.company_name,
                job_description=request.job_description
            )
            
            result.fraud_score = fraud_analysis.get("fraud_score", 0.0)
            result.fraud_indicators = fraud_analysis.get("indicators", [])
            result.is_fraudulent = fraud_analysis.get("is_fraudulent", False)
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

