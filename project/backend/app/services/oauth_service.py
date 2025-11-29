"""
OAuth Service
Handles OAuth authentication with Google and LinkedIn
"""

from typing import Dict, Any, Optional
from app.core.singleton import APIConnectionManager
from app.core.config import settings


class OAuthService:
    """Service for OAuth authentication"""

    async def verify_google_token(self, access_token: str) -> Dict[str, Any]:
        """
        Verify Google OAuth token and get user info

        Args:
            access_token: Google OAuth access token

        Returns:
            User information from Google
        """
        api_manager = APIConnectionManager.get_instance()
        client = await api_manager.get_client()

        try:
            # Verify token with Google
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            user_info = response.json()

            return {
                "email": user_info.get("email"),
                "oauth_id": user_info.get("id"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
            }
        except Exception as e:
            raise ValueError(f"Failed to verify Google token: {str(e)}")

    async def verify_linkedin_token(self, access_token: str) -> Dict[str, Any]:
        """
        Verify LinkedIn OAuth token and get user info

        Args:
            access_token: LinkedIn OAuth access token

        Returns:
            User information from LinkedIn
        """
        api_manager = APIConnectionManager.get_instance()
        client = await api_manager.get_client()

        try:
            # Get user profile from LinkedIn
            response = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            user_info = response.json()

            return {
                "email": user_info.get("email"),
                "oauth_id": user_info.get("sub"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
            }
        except Exception as e:
            raise ValueError(f"Failed to verify LinkedIn token: {str(e)}")

    async def get_oauth_user_info(
        self, provider: str, access_token: str
    ) -> Dict[str, Any]:
        """
        Get user info from OAuth provider

        Args:
            provider: OAuth provider (google, linkedin)
            access_token: OAuth access token

        Returns:
            User information
        """
        if provider.lower() == "google":
            return await self.verify_google_token(access_token)
        elif provider.lower() == "linkedin":
            return await self.verify_linkedin_token(access_token)
        else:
            raise ValueError(f"Unsupported OAuth provider: {provider}")
