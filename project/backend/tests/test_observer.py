"""
Tests for observer pattern notifications
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from app.patterns.observer import UserAccountSubject, EventType, Observer


class MockObserver(Observer):
    """Mock observer for testing."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.notifications = []
    
    async def update(self, event_type, data):
        """Record notification."""
        self.notifications.append({
            "event_type": event_type,
            "data": data
        })


class TestObserverPattern:
    """Test observer pattern notifications."""
    
    @pytest.mark.asyncio
    async def test_credits_changed_notification(self):
        """Test that observers are notified when credits change."""
        # Setup
        subject = UserAccountSubject()
        observer = MockObserver(user_id=1)
        await subject.attach(observer)
        
        user_id = 1
        old_credits = 50
        new_credits = 150
        
        # Execute
        await subject.credits_changed(
            user_id=user_id,
            old_credits=old_credits,
            new_credits=new_credits
        )
        
        # Assert
        assert len(observer.notifications) == 1
        notification = observer.notifications[0]
        assert notification["event_type"] == EventType.CREDITS_CHANGED
        assert notification["data"]["user_id"] == user_id
        assert notification["data"]["old_credits"] == old_credits
        assert notification["data"]["new_credits"] == new_credits
        assert notification["data"]["change"] == new_credits - old_credits
    
    @pytest.mark.asyncio
    async def test_payment_complete_notification(self):
        """Test that observers are notified when payment completes."""
        # Setup
        subject = UserAccountSubject()
        observer = MockObserver(user_id=1)
        await subject.attach(observer)
        
        user_id = 1
        payment_id = "pi_test_1234567890"
        credits_purchased = 100
        
        # Execute
        await subject.payment_complete(
            user_id=user_id,
            payment_id=payment_id,
            credits_purchased=credits_purchased
        )
        
        # Assert
        assert len(observer.notifications) == 1
        notification = observer.notifications[0]
        assert notification["event_type"] == EventType.PAYMENT_COMPLETE
        assert notification["data"]["user_id"] == user_id
        assert notification["data"]["payment_id"] == payment_id
        assert notification["data"]["credits_purchased"] == credits_purchased
    
    @pytest.mark.asyncio
    async def test_multiple_observers_notified(self):
        """Test that all registered observers are notified."""
        # Setup
        subject = UserAccountSubject()
        observer1 = MockObserver(user_id=1)
        observer2 = MockObserver(user_id=1)
        observer3 = MockObserver(user_id=1)
        
        await subject.attach(observer1)
        await subject.attach(observer2)
        await subject.attach(observer3)
        
        # Execute
        await subject.credits_changed(
            user_id=1,
            old_credits=50,
            new_credits=150
        )
        
        # Assert
        assert len(observer1.notifications) == 1
        assert len(observer2.notifications) == 1
        assert len(observer3.notifications) == 1
        
        # All should have the same notification
        assert observer1.notifications[0] == observer2.notifications[0]
        assert observer2.notifications[0] == observer3.notifications[0]
    
    @pytest.mark.asyncio
    async def test_observer_detach(self):
        """Test that detached observers are not notified."""
        # Setup
        subject = UserAccountSubject()
        observer1 = MockObserver(user_id=1)
        observer2 = MockObserver(user_id=1)
        
        await subject.attach(observer1)
        await subject.attach(observer2)
        
        # Detach observer2
        await subject.detach(observer2)
        
        # Execute
        await subject.credits_changed(
            user_id=1,
            old_credits=50,
            new_credits=150
        )
        
        # Assert
        assert len(observer1.notifications) == 1
        assert len(observer2.notifications) == 0
    
    @pytest.mark.asyncio
    async def test_observer_integration_with_webhook(self):
        """Test observer integration with webhook processing."""
        # Setup
        from app.patterns.observer import user_event_subject
        
        observer = MockObserver(user_id=1)
        await user_event_subject.attach(observer)
        
        user_id = 1
        old_credits = 50
        new_credits = 150
        payment_id = "pi_test_123"
        credits_purchased = 100
        
        # Execute - simulate webhook processing
        await user_event_subject.credits_changed(
            user_id=user_id,
            old_credits=old_credits,
            new_credits=new_credits
        )
        
        await user_event_subject.payment_complete(
            user_id=user_id,
            payment_id=payment_id,
            credits_purchased=credits_purchased
        )
        
        # Assert
        assert len(observer.notifications) == 2
        assert observer.notifications[0]["event_type"] == EventType.CREDITS_CHANGED
        assert observer.notifications[1]["event_type"] == EventType.PAYMENT_COMPLETE
        
        # Cleanup
        await user_event_subject.detach(observer)
    
    @pytest.mark.asyncio
    async def test_observer_error_handling(self):
        """Test that observer errors don't break the notification system."""
        # Setup
        subject = UserAccountSubject()
        
        # Create observer that raises an error
        error_observer = MagicMock()
        error_observer.update = AsyncMock(side_effect=Exception("Observer error"))
        
        # Create normal observer
        normal_observer = MockObserver(user_id=1)
        
        await subject.attach(error_observer)
        await subject.attach(normal_observer)
        
        # Execute - should not raise exception
        try:
            await subject.credits_changed(
                user_id=1,
                old_credits=50,
                new_credits=150
            )
        except Exception:
            pytest.fail("Observer error should not break notification system")
        
        # Assert - normal observer should still be notified
        assert len(normal_observer.notifications) == 1

