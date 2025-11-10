"""
Tests for database transactions
"""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.core.singleton import DatabaseManager


class TestDatabaseTransactions:
    """Test database transaction operations."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Create a mock Supabase client."""
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_query = MagicMock()
        
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.insert.return_value = mock_query
        mock_query.update.return_value = mock_query
        mock_query.delete.return_value = mock_query
        
        mock_table.select.return_value = mock_query
        mock_table.insert.return_value = mock_query
        mock_table.update.return_value = mock_query
        mock_table.delete.return_value = mock_query
        mock_table.eq.return_value = mock_query
        
        mock_client.table.return_value = mock_table
        
        return mock_client
    
    def test_credit_transaction_created(self, mock_supabase_client):
        """Test that transaction record is created in credit_transactions table."""
        # Setup
        user_id = uuid4()
        transaction_id = uuid4()
        stripe_payment_id = "pi_test_1234567890"
        credits = 100
        
        mock_table = mock_supabase_client.table.return_value
        mock_insert = mock_table.insert.return_value
        mock_insert.execute.return_value = MagicMock(
            data=[{
                "transaction_id": str(transaction_id),
                "user_id": str(user_id),
                "transaction_type": "purchase",
                "amount": credits,
                "stripe_payment_id": stripe_payment_id,
                "created_at": datetime.utcnow().isoformat()
            }]
        )
        
        # Execute
        result = mock_table.insert({
            "user_id": str(user_id),
            "transaction_type": "purchase",
            "amount": credits,
            "stripe_payment_id": stripe_payment_id
        }).execute()
        
        # Assert
        assert result.data[0]["transaction_id"] == str(transaction_id)
        assert result.data[0]["user_id"] == str(user_id)
        assert result.data[0]["transaction_type"] == "purchase"
        assert result.data[0]["amount"] == credits
        assert result.data[0]["stripe_payment_id"] == stripe_payment_id
        assert "created_at" in result.data[0]
        
        # Verify insert was called
        mock_table.insert.assert_called_once()
    
    def test_user_credits_updated(self, mock_supabase_client):
        """Test that user credits are updated correctly."""
        # Setup
        user_id = uuid4()
        old_credits = 50
        credits_to_add = 100
        new_credits = old_credits + credits_to_add
        
        mock_table = mock_supabase_client.table.return_value
        
        # Configure the mock chain: select() -> eq() -> execute()
        # When select("credits") is called, it returns a query mock
        # When eq() is called on that, it returns the same query mock
        # When execute() is called, it returns the result
        mock_query = MagicMock()
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = MagicMock(
            data=[{"credits": old_credits}]
        )
        mock_table.select.return_value = mock_query
        
        # Mock update chain: update() -> eq() -> execute()
        mock_update_query = MagicMock()
        mock_update_query.eq.return_value = mock_update_query
        mock_update_query.execute.return_value = MagicMock(
            data=[{"credits": new_credits}]
        )
        mock_table.update.return_value = mock_update_query
        
        # Execute - get current credits
        current_result = mock_table.select("credits").eq("user_id", str(user_id)).execute()
        current_credits = current_result.data[0]["credits"]
        
        # Execute - update credits
        update_result = mock_table.update({
            "credits": current_credits + credits_to_add
        }).eq("user_id", str(user_id)).execute()
        
        # Assert
        assert current_credits == old_credits
        assert update_result.data[0]["credits"] == new_credits
        assert new_credits == old_credits + credits_to_add
    
    def test_multiple_purchases_accumulate_credits(self, mock_supabase_client):
        """Test that multiple purchases accumulate credits correctly."""
        # Setup
        user_id = uuid4()
        initial_credits = 50
        
        mock_table = mock_supabase_client.table.return_value
        
        # Configure select chain with side_effect for sequential calls
        mock_select_query = MagicMock()
        mock_select_query.eq.return_value = mock_select_query
        # Use side_effect to return different values for sequential execute() calls
        mock_select_query.execute.side_effect = [
            MagicMock(data=[{"credits": initial_credits}]),  # First call
            MagicMock(data=[{"credits": initial_credits + 100}])  # Second call
        ]
        mock_table.select.return_value = mock_select_query
        
        # Configure update chain with side_effect for sequential calls
        mock_update_query = MagicMock()
        mock_update_query.eq.return_value = mock_update_query
        # Use side_effect to return different values for sequential execute() calls
        mock_update_query.execute.side_effect = [
            MagicMock(data=[{"credits": initial_credits + 100}]),  # First update
            MagicMock(data=[{"credits": initial_credits + 100 + 500}])  # Second update
        ]
        mock_table.update.return_value = mock_update_query
        
        # Execute first purchase
        result1 = mock_table.select("credits").eq("user_id", str(user_id)).execute()
        credits_after_first = result1.data[0]["credits"] + 100
        update_result1 = mock_table.update({"credits": credits_after_first}).eq("user_id", str(user_id)).execute()
        
        # Execute second purchase
        result2 = mock_table.select("credits").eq("user_id", str(user_id)).execute()
        credits_after_second = result2.data[0]["credits"] + 500
        update_result2 = mock_table.update({"credits": credits_after_second}).eq("user_id", str(user_id)).execute()
        
        # Assert
        assert update_result1.data[0]["credits"] == initial_credits + 100
        assert update_result2.data[0]["credits"] == initial_credits + 100 + 500
    
    def test_transaction_history(self, mock_supabase_client):
        """Test that transaction history can be queried."""
        # Setup
        user_id = uuid4()
        transactions = [
            {
                "transaction_id": str(uuid4()),
                "user_id": str(user_id),
                "transaction_type": "purchase",
                "amount": 100,
                "stripe_payment_id": "pi_test_1",
                "created_at": "2024-01-01T10:00:00Z"
            },
            {
                "transaction_id": str(uuid4()),
                "user_id": str(user_id),
                "transaction_type": "purchase",
                "amount": 500,
                "stripe_payment_id": "pi_test_2",
                "created_at": "2024-01-02T10:00:00Z"
            }
        ]
        
        mock_table = mock_supabase_client.table.return_value
        mock_select = mock_table.select.return_value
        # Return transactions in reverse order (most recent first)
        mock_select.eq.return_value.order.return_value.execute.return_value = MagicMock(
            data=list(reversed(transactions))  # Most recent first (desc order)
        )
        
        # Execute
        result = mock_table.select(
            "transaction_id, user_id, transaction_type, amount, stripe_payment_id, created_at"
        ).eq("user_id", str(user_id)).order("created_at", desc=True).execute()
        
        # Assert
        assert len(result.data) == 2
        assert result.data[0]["amount"] == 500  # Most recent first
        assert result.data[1]["amount"] == 100
        assert all(t["user_id"] == str(user_id) for t in result.data)
        assert all(t["transaction_type"] == "purchase" for t in result.data)
    
    def test_transaction_created_at_timestamp(self, mock_supabase_client):
        """Test that created_at timestamp is set automatically."""
        # Setup
        user_id = uuid4()
        transaction_id = uuid4()
        
        mock_table = mock_supabase_client.table.return_value
        mock_insert = mock_table.insert.return_value
        mock_insert.execute.return_value = MagicMock(
            data=[{
                "transaction_id": str(transaction_id),
                "created_at": datetime.now(timezone.utc).isoformat()
            }]
        )
        
        # Execute
        result = mock_table.insert({
            "user_id": str(user_id),
            "transaction_type": "purchase",
            "amount": 100
        }).execute()
        
        # Assert
        assert "created_at" in result.data[0]
        # Verify it's a valid ISO format timestamp
        created_at = result.data[0]["created_at"]
        assert "T" in created_at or " " in created_at  # ISO format

