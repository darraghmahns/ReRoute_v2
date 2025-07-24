import time

import pytest
import requests

BASE_URL = "http://localhost:8000"


@pytest.mark.integration
def get_access_token():
    unique_email = f"chat{int(time.time())}@example.com"
    register_data = {
        "email": unique_email,
        "password": "testpassword123",
        "full_name": "Chat Test User",
    }
    requests.post(f"{BASE_URL}/auth/register", json=register_data)
    login_data = {"username": unique_email, "password": "testpassword123"}
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.mark.integration
def test_chat_message():
    print("\n🧪 Testing /chat/message endpoint")
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"messages": [{"role": "user", "content": "Hello, who are you?"}]}
    response = requests.post(f"{BASE_URL}/chat/message", json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert data["message"]["role"] == "assistant"
    assert isinstance(data["message"]["content"], str)


@pytest.mark.integration
def test_chat_history_and_clear():
    print("\n🧪 Testing /chat/history and /chat/history DELETE endpoints")
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    # Send a message
    payload = {
        "messages": [{"role": "user", "content": "What is the capital of France?"}]
    }
    requests.post(f"{BASE_URL}/chat/message", json=payload, headers=headers)
    # Get history
    response = requests.get(f"{BASE_URL}/chat/history", headers=headers)
    print(f"History status: {response.status_code}")
    print(f"History: {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["history"], list)
    assert any(msg["role"] == "user" for msg in data["history"])
    assert any(msg["role"] == "assistant" for msg in data["history"])
    # Clear history
    response = requests.delete(f"{BASE_URL}/chat/history", headers=headers)
    print(f"Clear status: {response.status_code}")
    print(f"Clear response: {response.text}")
    assert response.status_code == 200
    # History should now be empty
    response = requests.get(f"{BASE_URL}/chat/history", headers=headers)
    data = response.json()
    assert data["history"] == []


if __name__ == "__main__":
    test_chat_message()
    test_chat_history_and_clear()
