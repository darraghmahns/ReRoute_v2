import os
import sys
from pathlib import Path

import requests

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.config import settings


def test_strava_configuration():
    """Test Strava configuration and basic API connectivity"""
    print("🧪 Testing Strava Configuration")
    print("=" * 40)

    # Check if Strava credentials are set
    client_id = settings.STRAVA_CLIENT_ID
    client_secret = settings.STRAVA_CLIENT_SECRET
    redirect_uri = settings.STRAVA_REDIRECT_URI
    webhook_secret = settings.STRAVA_WEBHOOK_SECRET

    if client_id == "changeme" or client_secret == "changeme":
        print("❌ Strava credentials not configured!")
        return False

    print(f"✅ Strava Client ID: {client_id}")
    print(f"✅ Strava Client Secret: {client_secret[:10]}...")
    print(f"✅ Redirect URI: {redirect_uri}")
    print(f"✅ Webhook Secret: {webhook_secret[:10]}...")

    # Test basic API connectivity (without auth token)
    try:
        # Test the Strava API base URL
        response = requests.get("https://www.strava.com/api/v3/athlete", timeout=5)
        print("✅ Strava API is accessible")
        return True

    except Exception as e:
        print(f"❌ Strava API test failed: {str(e)}")
        return False


def test_mapbox_configuration():
    """Test Mapbox configuration"""
    print("\n🗺️  Testing Mapbox Configuration")
    print("=" * 40)

    api_key = settings.MAPBOX_API_KEY
    if api_key == "changeme" or not api_key:
        print("❌ Mapbox API key not configured!")
        return False

    print(f"✅ Mapbox API key configured: {api_key[:20]}...")

    # Test basic Mapbox API connectivity
    try:
        # Test with a simple geocoding request
        test_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/Los%20Angeles.json?access_token={api_key}"
        response = requests.get(test_url, timeout=5)

        if response.status_code == 200:
            print("✅ Mapbox API connection successful!")
            return True
        else:
            print(f"❌ Mapbox API test failed with status: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Mapbox API test failed: {str(e)}")
        return False


def test_environment_loading():
    """Test that environment variables are loading correctly"""
    print("\n🔧 Testing Environment Configuration")
    print("=" * 40)

    # Test a few key settings
    print(f"OpenAI API Key: {settings.OPENAI_API_KEY[:20]}...")
    print(f"Strava Client ID: {settings.STRAVA_CLIENT_ID}")
    print(f"Mapbox API Key: {settings.MAPBOX_API_KEY[:20]}...")
    print(f"Database: {settings.POSTGRES_DB}")
    print(f"Redis URL: {settings.REDIS_URL}")
    print(f"JWT Algorithm: {settings.ALGORITHM}")
    print(f"Token Expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")

    # Check if .env file exists
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found - using default values")


if __name__ == "__main__":
    test_environment_loading()
    test_strava_configuration()
    test_mapbox_configuration()
