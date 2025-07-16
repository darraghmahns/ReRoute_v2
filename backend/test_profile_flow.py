import requests
import json
import time

base_url = "http://localhost:8000"

def test_profile_flow():
    print("🧪 Testing Full Profile Management Flow")
    print("=" * 50)
    
    # 1. Register and login
    print("\n1. Registering and logging in...")
    unique_email = f"profile{int(time.time())}@example.com"
    
    # Register
    register_data = {
        "email": unique_email,
        "password": "testpassword123",
        "full_name": "Profile Test User"
    }
    
    response = requests.post(f"{base_url}/auth/register", json=register_data)
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.text}")
        return
    
    # Login
    login_data = {
        "username": unique_email,
        "password": "testpassword123"
    }
    
    response = requests.post(f"{base_url}/auth/login", data=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    token_data = response.json()
    access_token = token_data['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}
    print(f"✅ Login successful")
    
    # 2. Try to get profile (should fail initially)
    print("\n2. Testing profile retrieval...")
    response = requests.get(f"{base_url}/profiles/me", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 404:
        print("✅ Profile not found (expected for new user)")
    else:
        print(f"Unexpected response: {response.text}")
    
    # 3. Update profile
    print("\n3. Creating/updating profile...")
    profile_data = {
        "age": 30,
        "gender": "male",
        "weight_lbs": 165.0,
        "height_ft": 5,
        "height_in": 11,
        "cycling_experience": "intermediate",
        "fitness_level": "moderate"
    }
    
    response = requests.put(f"{base_url}/profiles/me", json=profile_data, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        profile = response.json()
        print(f"✅ Profile updated successfully")
        print(f"   Age: {profile.get('age')}")
        print(f"   Weight: {profile.get('weight_lbs')} lbs")
        print(f"   Experience: {profile.get('cycling_experience')}")
    else:
        print(f"❌ Profile update failed: {response.text}")
        return
    
    # 4. Complete profile step by step
    print("\n4. Completing profile step by step...")
    
    # Step 1: Personal information
    step1_data = {
        "step": 1,
        "data": {
            "age": 30,
            "gender": "male",
            "weight_lbs": 165.0,
            "height_ft": 5,
            "height_in": 11
        }
    }
    
    response = requests.post(f"{base_url}/profiles/complete", json=step1_data, headers=headers)
    print(f"Step 1 Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Step 1 completed")
    else:
        print(f"❌ Step 1 failed: {response.text}")
    
    # Step 2: Goals and experience
    step2_data = {
        "step": 2,
        "data": {
            "cycling_experience": "intermediate",
            "fitness_level": "moderate",
            "primary_goals": "Improve endurance and complete century rides"
        }
    }
    
    response = requests.post(f"{base_url}/profiles/complete", json=step2_data, headers=headers)
    print(f"Step 2 Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Step 2 completed")
    else:
        print(f"❌ Step 2 failed: {response.text}")
    
    # Step 3: Health assessment
    step3_data = {
        "step": 3,
        "data": {
            "injury_history": "Minor knee strain 2 years ago",
            "medical_conditions": "None",
            "current_fitness_assessment": "Good cardiovascular fitness, needs strength training"
        }
    }
    
    response = requests.post(f"{base_url}/profiles/complete", json=step3_data, headers=headers)
    print(f"Step 3 Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Step 3 completed")
    else:
        print(f"❌ Step 3 failed: {response.text}")
    
    # Step 4: Schedule
    step4_data = {
        "step": 4,
        "data": {
            "weekly_training_hours": 8.0,
            "preferred_training_days": "Monday, Wednesday, Friday, Sunday",
            "time_availability": {
                "weekdays": "6:00 AM - 8:00 AM",
                "weekends": "8:00 AM - 12:00 PM"
            }
        }
    }
    
    response = requests.post(f"{base_url}/profiles/complete", json=step4_data, headers=headers)
    print(f"Step 4 Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Step 4 completed")
    else:
        print(f"❌ Step 4 failed: {response.text}")
    
    # Step 5: Equipment and preferences
    step5_data = {
        "step": 5,
        "data": {
            "nutrition_preferences": "High protein, moderate carbs",
            "equipment_available": "Road bike, trainer, heart rate monitor, power meter",
            "training_preferences": {
                "preferred_intensity": "moderate",
                "recovery_days": "Tuesday, Thursday",
                "cross_training": "yoga, swimming"
            }
        }
    }
    
    response = requests.post(f"{base_url}/profiles/complete", json=step5_data, headers=headers)
    print(f"Step 5 Status: {response.status_code}")
    if response.status_code == 200:
        profile = response.json()
        print("✅ Step 5 completed")
        print(f"   Profile completed: {profile.get('profile_completed')}")
    else:
        print(f"❌ Step 5 failed: {response.text}")
    
    # 5. Get final profile
    print("\n5. Retrieving final profile...")
    response = requests.get(f"{base_url}/profiles/me", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        profile = response.json()
        print(f"✅ Profile retrieved successfully")
        print(f"   Age: {profile.get('age')}")
        print(f"   Experience: {profile.get('cycling_experience')}")
        print(f"   Goals: {profile.get('primary_goals')}")
        print(f"   Weekly hours: {profile.get('weekly_training_hours')}")
        print(f"   Completed: {profile.get('profile_completed')}")
    else:
        print(f"❌ Profile retrieval failed: {response.text}")
    
    print("\n" + "=" * 50)
    print("🎉 Profile management flow test completed!")

if __name__ == "__main__":
    test_profile_flow() 