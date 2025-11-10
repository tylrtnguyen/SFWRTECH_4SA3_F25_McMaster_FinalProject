"""
Strategy Pattern
Switch job matching algorithms based on user-selected priorities/goals
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.models.schemas import Job, UserPreferences


class JobMatchingStrategy(ABC):
    """Abstract strategy for job matching algorithms"""
    
    @abstractmethod
    async def match_jobs(
        self,
        user_preferences: UserPreferences,
        available_jobs: List[Job]
    ) -> List[Dict[str, Any]]:
        """
        Match jobs based on strategy
        
        Returns:
            List of matched jobs with scores
        """
        pass


class SalaryPriorityStrategy(JobMatchingStrategy):
    """Strategy prioritizing jobs with higher salary"""
    
    async def match_jobs(
        self,
        user_preferences: UserPreferences,
        available_jobs: List[Job]
    ) -> List[Dict[str, Any]]:
        """Match jobs prioritizing salary"""
        matched = []
        
        for job in available_jobs:
            score = 0.0
            
            # Salary weight: 60%
            if job.salary_max:
                if user_preferences.min_salary:
                    if job.salary_max >= user_preferences.min_salary:
                        score += 0.6 * (min(job.salary_max / (user_preferences.min_salary * 1.5), 1.0))
                else:
                    score += 0.6
            
            # Location weight: 20%
            if job.location and user_preferences.preferred_locations:
                if job.location in user_preferences.preferred_locations:
                    score += 0.2
            
            # Skills match weight: 20%
            if job.required_skills and user_preferences.skills:
                matching_skills = set(job.required_skills) & set(user_preferences.skills)
                if job.required_skills:
                    score += 0.2 * (len(matching_skills) / len(job.required_skills))
            
            matched.append({
                "job": job,
                "score": score,
                "strategy": "salary_priority"
            })
        
        # Sort by score descending
        matched.sort(key=lambda x: x["score"], reverse=True)
        return matched


class LocationPriorityStrategy(JobMatchingStrategy):
    """Strategy prioritizing jobs in preferred locations"""
    
    async def match_jobs(
        self,
        user_preferences: UserPreferences,
        available_jobs: List[Job]
    ) -> List[Dict[str, Any]]:
        """Match jobs prioritizing location"""
        matched = []
        
        for job in available_jobs:
            score = 0.0
            
            # Location weight: 60%
            if job.location and user_preferences.preferred_locations:
                if job.location in user_preferences.preferred_locations:
                    score += 0.6
            elif not user_preferences.preferred_locations:
                score += 0.6  # No preference means all locations acceptable
            
            # Skills match weight: 30%
            if job.required_skills and user_preferences.skills:
                matching_skills = set(job.required_skills) & set(user_preferences.skills)
                if job.required_skills:
                    score += 0.3 * (len(matching_skills) / len(job.required_skills))
            
            # Salary weight: 10%
            if job.salary_max and user_preferences.min_salary:
                if job.salary_max >= user_preferences.min_salary:
                    score += 0.1
            
            matched.append({
                "job": job,
                "score": score,
                "strategy": "location_priority"
            })
        
        matched.sort(key=lambda x: x["score"], reverse=True)
        return matched


class SkillsMatchStrategy(JobMatchingStrategy):
    """Strategy prioritizing jobs with best skills match"""
    
    async def match_jobs(
        self,
        user_preferences: UserPreferences,
        available_jobs: List[Job]
    ) -> List[Dict[str, Any]]:
        """Match jobs prioritizing skills match"""
        matched = []
        
        for job in available_jobs:
            score = 0.0
            
            # Skills match weight: 70%
            if job.required_skills and user_preferences.skills:
                matching_skills = set(job.required_skills) & set(user_preferences.skills)
                if job.required_skills:
                    score += 0.7 * (len(matching_skills) / len(job.required_skills))
            elif not job.required_skills:
                score += 0.7  # No requirements means all skills acceptable
            
            # Location weight: 15%
            if job.location and user_preferences.preferred_locations:
                if job.location in user_preferences.preferred_locations:
                    score += 0.15
            
            # Salary weight: 15%
            if job.salary_max and user_preferences.min_salary:
                if job.salary_max >= user_preferences.min_salary:
                    score += 0.15
            
            matched.append({
                "job": job,
                "score": score,
                "strategy": "skills_match"
            })
        
        matched.sort(key=lambda x: x["score"], reverse=True)
        return matched


class BalancedStrategy(JobMatchingStrategy):
    """Strategy with balanced consideration of all factors"""
    
    async def match_jobs(
        self,
        user_preferences: UserPreferences,
        available_jobs: List[Job]
    ) -> List[Dict[str, Any]]:
        """Match jobs with balanced approach"""
        matched = []
        
        for job in available_jobs:
            score = 0.0
            
            # Skills match weight: 40%
            if job.required_skills and user_preferences.skills:
                matching_skills = set(job.required_skills) & set(user_preferences.skills)
                if job.required_skills:
                    score += 0.4 * (len(matching_skills) / len(job.required_skills))
            
            # Salary weight: 30%
            if job.salary_max:
                if user_preferences.min_salary:
                    if job.salary_max >= user_preferences.min_salary:
                        score += 0.3 * (min(job.salary_max / (user_preferences.min_salary * 1.3), 1.0))
                else:
                    score += 0.3
            
            # Location weight: 30%
            if job.location and user_preferences.preferred_locations:
                if job.location in user_preferences.preferred_locations:
                    score += 0.3
            elif not user_preferences.preferred_locations:
                score += 0.3
            
            matched.append({
                "job": job,
                "score": score,
                "strategy": "balanced"
            })
        
        matched.sort(key=lambda x: x["score"], reverse=True)
        return matched


class JobMatchingContext:
    """Context that uses strategy pattern to switch between matching algorithms"""
    
    def __init__(self, strategy: JobMatchingStrategy):
        self._strategy = strategy
    
    def set_strategy(self, strategy: JobMatchingStrategy):
        """Change the matching strategy"""
        self._strategy = strategy
    
    async def execute_matching(
        self,
        user_preferences: UserPreferences,
        available_jobs: List[Job]
    ) -> List[Dict[str, Any]]:
        """Execute matching using current strategy"""
        return await self._strategy.match_jobs(user_preferences, available_jobs)
    
    @staticmethod
    def get_strategy_by_name(strategy_name: str) -> JobMatchingStrategy:
        """Get strategy instance by name"""
        strategies = {
            "salary": SalaryPriorityStrategy(),
            "location": LocationPriorityStrategy(),
            "skills": SkillsMatchStrategy(),
            "balanced": BalancedStrategy()
        }
        return strategies.get(strategy_name.lower(), BalancedStrategy())

