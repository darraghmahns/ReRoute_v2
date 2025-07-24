import json
import time

import pytest
import requests

base_url = "http://localhost:8002"


@pytest.mark.integration
def test_strava_integration():
    print("🧪 Testing Strava Integration")
    print("=" * 50)

    # 1. Register and login
    print("\n1. Registering and logging in...")
    unique_email = f"strava{int(time.time())}@example.com"

    # Register
    register_data = {
        "email": unique_email,
        "password": "testpassword123",
        "full_name": "Strava Test User",
    }

    response = requests.post(f"{base_url}/auth/register", json=register_data)
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.text}")
        return

    # Login
    login_data = {"username": unique_email, "password": "testpassword123"}

    response = requests.post(f"{base_url}/auth/login", data=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return

    token_data = response.json()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print(f"✅ Login successful")

    # 2. Test Strava auth URL
    print("\n2. Testing Strava auth URL...")
    response = requests.get(f"{base_url}/strava/auth-url", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        auth_data = response.json()
        auth_url = auth_data.get("auth_url")
        print(f"✅ Auth URL generated: {auth_url[:50]}...")
    else:
        print(f"❌ Auth URL failed: {response.text}")
        return

    # 3. Test activities endpoint (should fail without Strava connection)
    print("\n3. Testing activities endpoint (should fail without connection)...")
    response = requests.get(f"{base_url}/strava/activities", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 400:
        print("✅ Correctly requires Strava connection")
    else:
        print(f"Unexpected response: {response.text}")

    # 4. Test disconnect (should work even without connection)
    print("\n4. Testing disconnect endpoint...")
    response = requests.delete(f"{base_url}/strava/disconnect", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Disconnect endpoint working")
    else:
        print(f"❌ Disconnect failed: {response.text}")

    print("\n" + "=" * 50)
    print("🎉 Strava integration test completed!")
    print("\nTo test full Strava flow:")
    print("1. Visit the auth URL in your browser")
    print("2. Authorize the app")
    print("3. The callback will be handled by your frontend")
    print("4. Then you can test /strava/sync and /strava/activities")


if __name__ == "__main__":
    test_strava_integration()
