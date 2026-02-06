from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from app.config import settings
from app.instagram_client import InstagramClient
import urllib.parse

app = FastAPI(title="Instagram Metrics Retrieval")

# Initialize Instagram client
ig_client = InstagramClient(
    app_id=settings.FACEBOOK_APP_ID,
    app_secret=settings.FACEBOOK_APP_SECRET
)

@app.get("/")
async def root():
    return {"message": "Instagram Metrics API. Visit /auth/login to start."}

@app.get("/auth/login")
async def login():
    """Generate Facebook OAuth URL and redirect user"""
    oauth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth?"
        f"client_id={settings.FACEBOOK_APP_ID}&"
        f"redirect_uri={urllib.parse.quote(settings.REDIRECT_URI)}&"
        f"scope=instagram_basic,instagram_manage_insights,pages_show_list,pages_read_engagement&"
        f"response_type=code"
    )

    # Return HTML with clickable link
    html_content = f"""
    <html>
        <head><title>Instagram Login</title></head>
        <body>
            <h2>Click the link below to authenticate with Instagram:</h2>
            <p><a href="{oauth_url}">Login with Facebook/Instagram</a></p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/auth/callback")
async def callback(code: str):
    """Handle OAuth callback and fetch metrics"""
    try:
        print("\n" + "="*80)
        print("STEP 1: Exchanging code for access token...")
        print("="*80)

        # Exchange code for short-lived token
        short_token = await ig_client.exchange_code_for_token(code, settings.REDIRECT_URI)
        print("✓ Got short-lived token")

        # Exchange for long-lived token
        access_token = await ig_client.get_long_lived_token(short_token)
        print("✓ Got long-lived token (valid for 60 days)")

        print("\n" + "="*80)
        print("STEP 2: Getting Instagram Business Account ID...")
        print("="*80)

        # Get Instagram account
        ig_account = await ig_client.get_instagram_account_id(access_token)
        if not ig_account:
            raise HTTPException(status_code=404, detail="No Instagram Business Account found")

        instagram_account_id = ig_account["instagram_account_id"]
        page_token = ig_account["page_access_token"]
        print(f"✓ Instagram Account ID: {instagram_account_id}")

        print("\n" + "="*80)
        print("STEP 3: Fetching latest 5 posts...")
        print("="*80)

        # Get latest 5 posts
        media_posts = await ig_client.get_latest_media(instagram_account_id, page_token, limit=5)
        print(f"✓ Found {len(media_posts)} posts")

        print("\n" + "="*80)
        print("STEP 4: Fetching engagement metrics for each post...")
        print("="*80 + "\n")

        # Fetch insights for each post
        for i, post in enumerate(media_posts, 1):
            media_id = post["id"]
            media_type = post["media_type"]

            print(f"\n📸 POST {i}:")
            print(f"   Type: {media_type}")
            print(f"   Posted: {post.get('timestamp', 'N/A')}")
            print(f"   URL: {post.get('permalink', 'N/A')}")
            if post.get('caption'):
                caption = post['caption'][:100] + "..." if len(post['caption']) > 100 else post['caption']
                print(f"   Caption: {caption}")

            # Get metrics
            insights = await ig_client.get_media_insights(media_id, page_token, media_type)

            # Extract individual metrics
            engagement = insights.get("engagement", 0)
            impressions = insights.get("impressions", 0)
            reach = insights.get("reach", 0)
            saved = insights.get("saved", 0)

            print(f"\n   📊 ENGAGEMENT METRICS:")
            print(f"      Total Engagement: {engagement}")
            print(f"      Reach: {reach:,} accounts")
            print(f"      Impressions: {impressions:,}")
            print(f"      Saved: {saved}")

            if media_type == "VIDEO":
                video_views = insights.get("video_views", 0)
                print(f"      Video Views: {video_views:,}")

            # Calculate engagement rate
            if reach > 0:
                engagement_rate = (engagement / reach) * 100
                print(f"      Engagement Rate: {engagement_rate:.2f}%")

            print("\n   " + "-"*70)

        print("\n" + "="*80)
        print("✅ COMPLETED! Check the metrics above.")
        print("="*80 + "\n")

        return HTMLResponse(content="""
        <html>
            <head><title>Success</title></head>
            <body>
                <h2>✅ Success!</h2>
                <p>Check your terminal/console for the engagement metrics.</p>
                <p><a href="/">Back to home</a></p>
            </body>
        </html>
        """)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))