import httpx
from typing import Dict, List, Optional

class InstagramClient:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://graph.facebook.com/v19.0"

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> str:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/oauth/access_token",
                params={
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "code": code,
                    "redirect_uri": redirect_uri
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["access_token"]

    async def get_long_lived_token(self, short_token: str) -> str:
        """Exchange short-lived token for long-lived token (60 days)"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "fb_exchange_token": short_token
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["access_token"]

    async def get_instagram_account_id(self, access_token: str) -> Optional[Dict]:
        """Get Instagram Business Account ID from Facebook Pages"""
        async with httpx.AsyncClient() as client:
            # Get user's pages
            response = await client.get(
                f"{self.base_url}/me/accounts",
                params={"access_token": access_token}
            )
            response.raise_for_status()
            pages = response.json().get("data", [])

            # Find page with Instagram account
            for page in pages:
                page_id = page["id"]
                page_token = page["access_token"]

                # Check if page has Instagram account
                ig_response = await client.get(
                    f"{self.base_url}/{page_id}",
                    params={
                        "fields": "instagram_business_account",
                        "access_token": page_token
                    }
                )
                ig_response.raise_for_status()
                ig_data = ig_response.json()

                if "instagram_business_account" in ig_data:
                    return {
                        "instagram_account_id": ig_data["instagram_business_account"]["id"],
                        "page_access_token": page_token
                    }

            return None

    async def get_latest_media(self, instagram_account_id: str, access_token: str, limit: int = 5) -> List[Dict]:
        """Get latest media posts"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{instagram_account_id}/media",
                params={
                    "fields": "id,media_type,media_url,permalink,timestamp,caption",
                    "limit": limit,
                    "access_token": access_token
                }
            )
            response.raise_for_status()
            return response.json().get("data", [])

    async def get_media_insights(self, media_id: str, access_token: str, media_type: str) -> Dict:
        """Get insights for a specific media post"""
        # Different metrics for different media types
        if media_type == "VIDEO":
            metrics = "engagement,impressions,reach,saved,video_views"
        else:
            metrics = "engagement,impressions,reach,saved"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{media_id}/insights",
                params={
                    "metric": metrics,
                    "access_token": access_token
                }
            )
            response.raise_for_status()
            data = response.json().get("data", [])

            # Convert to dict
            insights = {}
            for item in data:
                insights[item["name"]] = item["values"][0]["value"]

            return insights