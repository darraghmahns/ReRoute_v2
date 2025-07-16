import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.config import settings
import openai

def test_openai_configuration():
    """Test OpenAI configuration and basic API connectivity"""
    print("🧪 Testing OpenAI Configuration")
    print("=" * 40)
    
    # Check if API key is set
    api_key = settings.OPENAI_API_KEY
    if api_key == "changeme" or not api_key:
        print("❌ OpenAI API key not configured!")
        print("Please create a .env file with your OpenAI API key")
        return False
    
    print(f"✅ OpenAI API key configured: {api_key[:20]}...")
    
    # Test basic API connectivity
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'Hello from Reroute!'"}
            ],
            max_tokens=10
        )
        
        print("✅ OpenAI API connection successful!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API test failed: {str(e)}")
        return False

def test_environment_loading():
    """Test that environment variables are loading correctly"""
    print("\n🔧 Testing Environment Configuration")
    print("=" * 40)
    
    # Test a few key settings
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
        print("Create a .env file using the content from env_setup.txt")

if __name__ == "__main__":
    test_environment_loading()
    test_openai_configuration() 