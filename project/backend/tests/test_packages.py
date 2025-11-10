"""
Tests for credit package functionality
"""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock
from fastapi import status

from app.core.config import settings


class TestCreditPackages:
    """Test credit package configuration and validation."""
    
    def test_package_configuration(self):
        """Test that credit packages are configured correctly."""
        # Assert
        assert "100" in settings.CREDIT_PACKAGES
        assert "500" in settings.CREDIT_PACKAGES
        assert "1000" in settings.CREDIT_PACKAGES
        
        # Test 100 credits package
        package_100 = settings.CREDIT_PACKAGES["100"]
        assert package_100["credits"] == 100
        assert package_100["amount_cents"] == 999
        assert package_100["name"] == "100 Credits Package"
        
        # Test 500 credits package
        package_500 = settings.CREDIT_PACKAGES["500"]
        assert package_500["credits"] == 500
        assert package_500["amount_cents"] == 3999
        assert package_500["name"] == "500 Credits Package"
        
        # Test 1000 credits package
        package_1000 = settings.CREDIT_PACKAGES["1000"]
        assert package_1000["credits"] == 1000
        assert package_1000["amount_cents"] == 6999
        assert package_1000["name"] == "1000 Credits Package"
    
    def test_package_pricing(self):
        """Test that package pricing is correct."""
        # Assert pricing per credit
        package_100 = settings.CREDIT_PACKAGES["100"]
        price_per_credit_100 = package_100["amount_cents"] / package_100["credits"]
        assert price_per_credit_100 == pytest.approx(9.99, rel=0.01)
        
        package_500 = settings.CREDIT_PACKAGES["500"]
        price_per_credit_500 = package_500["amount_cents"] / package_500["credits"]
        assert price_per_credit_500 == pytest.approx(7.998, rel=0.01)
        
        package_1000 = settings.CREDIT_PACKAGES["1000"]
        price_per_credit_1000 = package_1000["amount_cents"] / package_1000["credits"]
        assert price_per_credit_1000 == pytest.approx(6.999, rel=0.01)
    
    @pytest.mark.asyncio
    async def test_package_selection_validation(self, async_client, mock_user_id, mock_database_manager, mock_stripe_manager):
        """Test package selection validation."""
        # Test valid package IDs
        valid_packages = ["100", "500", "1000"]
        
        for package_id in valid_packages:
            package = settings.CREDIT_PACKAGES[package_id]
            
            mock_payment_intent = MagicMock()
            mock_payment_intent.id = f"pi_test_{package_id}"
            mock_payment_intent.client_secret = f"pi_test_{package_id}_secret"
            mock_payment_intent.amount = package["amount_cents"]
            mock_payment_intent.currency = "cad"
            mock_payment_intent.status = "requires_payment_method"
            
            mock_stripe_manager.get_client.return_value.PaymentIntent.create.return_value = mock_payment_intent
            
            mock_connection = mock_database_manager.get_connection.return_value
            mock_connection.table.return_value.insert.return_value.execute.return_value = MagicMock(
                data=[{"transaction_id": str(uuid4())}]
            )
            
            response = await async_client.post(
                "/api/v1/payments/intent",
                json={
                    "user_id": str(mock_user_id),
                    "amount": package["amount_cents"],
                    "credits": package["credits"]
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["amount"] == package["amount_cents"]
            assert data["credits"] == package["credits"]
    
    def test_package_metadata(self):
        """Test that packages have required metadata."""
        for package_id, package in settings.CREDIT_PACKAGES.items():
            assert "price_id" in package
            assert "credits" in package
            assert "amount_cents" in package
            assert "name" in package
            assert isinstance(package["credits"], int)
            assert isinstance(package["amount_cents"], int)
            assert package["credits"] > 0
            assert package["amount_cents"] > 0

