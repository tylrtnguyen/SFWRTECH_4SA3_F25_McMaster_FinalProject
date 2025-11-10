"""
Observer Pattern
Live updates to widget/dashboard when scores or credits change
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from enum import Enum
import asyncio
from datetime import datetime


class EventType(Enum):
    """Types of events that can be observed"""
    CREDITS_CHANGED = "credits_changed"
    SCORE_UPDATED = "score_updated"
    JOB_ANALYSIS_COMPLETE = "job_analysis_complete"
    PAYMENT_COMPLETE = "payment_complete"


class Observer(ABC):
    """Abstract observer interface"""
    
    @abstractmethod
    async def update(self, event_type: EventType, data: Dict[str, Any]):
        """Receive update notification"""
        pass


class Subject(ABC):
    """Abstract subject that observers can subscribe to"""
    
    def __init__(self):
        self._observers: List[Observer] = []
        self._lock = asyncio.Lock()
    
    async def attach(self, observer: Observer):
        """Attach an observer"""
        async with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)
    
    async def detach(self, observer: Observer):
        """Detach an observer"""
        async with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)
    
    async def notify(self, event_type: EventType, data: Dict[str, Any]):
        """Notify all observers"""
        async with self._lock:
            observers = self._observers.copy()
        
        # Notify all observers concurrently
        tasks = [observer.update(event_type, data) for observer in observers]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


class CreditsObserver(Observer):
    """Observer for credits changes"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.update_history: List[Dict[str, Any]] = []
    
    async def update(self, event_type: EventType, data: Dict[str, Any]):
        """Handle credits update"""
        if event_type == EventType.CREDITS_CHANGED:
            if data.get("user_id") == self.user_id:
                update_info = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": event_type.value,
                    "old_credits": data.get("old_credits"),
                    "new_credits": data.get("new_credits"),
                    "change": data.get("change")
                }
                self.update_history.append(update_info)
                # In a real implementation, this would push to WebSocket or SSE
                print(f"CreditsObserver: User {self.user_id} credits changed: {update_info}")


class ScoreObserver(Observer):
    """Observer for score updates"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.update_history: List[Dict[str, Any]] = []
    
    async def update(self, event_type: EventType, data: Dict[str, Any]):
        """Handle score update"""
        if event_type == EventType.SCORE_UPDATED:
            if data.get("user_id") == self.user_id:
                update_info = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": event_type.value,
                    "job_id": data.get("job_id"),
                    "fraud_score": data.get("fraud_score"),
                    "match_score": data.get("match_score")
                }
                self.update_history.append(update_info)
                # In a real implementation, this would push to WebSocket or SSE
                print(f"ScoreObserver: User {self.user_id} score updated: {update_info}")


class DashboardObserver(Observer):
    """Observer for dashboard updates (combines multiple events)"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.dashboard_updates: List[Dict[str, Any]] = []
    
    async def update(self, event_type: EventType, data: Dict[str, Any]):
        """Handle dashboard update"""
        if data.get("user_id") == self.user_id:
            update_info = {
                "timestamp": datetime.utcnow().isoformat(),
                "event": event_type.value,
                "data": data
            }
            self.dashboard_updates.append(update_info)
            # In a real implementation, this would push to WebSocket or SSE
            print(f"DashboardObserver: User {self.user_id} dashboard update: {update_info}")


class UserAccountSubject(Subject):
    """Subject for user account events (credits, scores, etc.)"""
    
    async def credits_changed(
        self,
        user_id: int,
        old_credits: int,
        new_credits: int
    ):
        """Notify observers of credits change"""
        change = new_credits - old_credits
        await self.notify(
            EventType.CREDITS_CHANGED,
            {
                "user_id": user_id,
                "old_credits": old_credits,
                "new_credits": new_credits,
                "change": change
            }
        )
    
    async def score_updated(
        self,
        user_id: int,
        job_id: str,
        fraud_score: float,
        match_score: float
    ):
        """Notify observers of score update"""
        await self.notify(
            EventType.SCORE_UPDATED,
            {
                "user_id": user_id,
                "job_id": job_id,
                "fraud_score": fraud_score,
                "match_score": match_score
            }
        )
    
    async def job_analysis_complete(
        self,
        user_id: int,
        job_id: str,
        analysis_result: Dict[str, Any]
    ):
        """Notify observers of job analysis completion"""
        await self.notify(
            EventType.JOB_ANALYSIS_COMPLETE,
            {
                "user_id": user_id,
                "job_id": job_id,
                "analysis": analysis_result
            }
        )
    
    async def payment_complete(
        self,
        user_id: int,
        payment_id: str,
        credits_purchased: int
    ):
        """Notify observers of payment completion"""
        await self.notify(
            EventType.PAYMENT_COMPLETE,
            {
                "user_id": user_id,
                "payment_id": payment_id,
                "credits_purchased": credits_purchased
            }
        )


# Global subject instance for user events
user_event_subject = UserAccountSubject()

