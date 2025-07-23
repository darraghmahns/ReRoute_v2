import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.services.openai_chat import openai_chat_service
from app.schemas.training import WorkoutType, Workout, TrainingWeek


class TrainingPlanGenerator:
    def __init__(self):
        self.openai_service = openai_chat_service

    def generate_plan(self, goal: str, weekly_hours: int, fitness_level: str = "intermediate", preferences: List[str] = None, strava_data: dict = None) -> Dict[str, Any]:
        """Generate a training plan using OpenAI"""
        
        # Create the prompt for OpenAI
        prompt = self._create_generation_prompt(goal, weekly_hours, fitness_level, preferences, strava_data)
        
        # Generate the plan using OpenAI
        response = self.openai_service.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert cycling coach. Generate structured training plans in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="gpt-4",
            max_tokens=2000,
            temperature=0.7
        )
        
        # Parse the response
        try:
            plan_data = self._parse_openai_response(response)
            return plan_data
        except Exception as e:
            # Fallback to a default plan if parsing fails
            return self._generate_fallback_plan(goal, weekly_hours)

    def _create_generation_prompt(self, goal: str, weekly_hours: int, fitness_level: str, preferences: List[str] = None, strava_data: dict = None) -> str:
        """Create the prompt for OpenAI"""
        
        preferences_text = ""
        if preferences:
            preferences_text = f"\nPreferences: {', '.join(preferences)}"
        
        # Add Strava data to the prompt if available
        strava_text = ""
        if strava_data and strava_data.get("connected"):
            activities = strava_data.get("recent_activities", [])
            activity_types = strava_data.get("activity_types", {})
            total_distance = strava_data.get("total_distance_m", 0)
            total_time = strava_data.get("total_time_s", 0)
            avg_heartrate = strava_data.get("avg_heartrate", 0)
            
            strava_text = f"""

STRAVA DATA ANALYSIS:
- Recent Activities: {len(activities)} activities analyzed
- Total Distance: {total_distance/1000:.1f} km
- Total Time: {total_time/3600:.1f} hours
- Average Heart Rate: {avg_heartrate:.0f} bpm
- Activity Types: {', '.join([f'{k} ({v})' for k, v in activity_types.items()])}

Recent Activity Details:
"""
            for i, act in enumerate(activities[:3], 1):  # Show last 3 activities
                strava_text += f"""
{i}. {act.get('name', 'Unknown Activity')}
   - Type: {act.get('type', 'Unknown')}
   - Distance: {act.get('distance_m', 0)/1000:.1f} km
   - Duration: {act.get('moving_time_s', 0)/60:.0f} minutes
   - Elevation: {act.get('total_elevation_gain_m', 0):.0f} m
   - Avg HR: {act.get('average_heartrate', 'N/A')} bpm
"""
            
            strava_text += f"""

PERSONALIZATION GUIDELINES:
- Consider the user's recent activity patterns and performance
- Build upon their current fitness level based on recent activities
- Account for their preferred activity types and distances
- Use their average heart rate zones to inform training intensity
- Consider their recent performance trends for progression planning
"""
        else:
            strava_text = """

Note: No Strava data available. Generating a general training plan.
"""
        
        prompt = f"""
Generate a 4-week cycling training plan with the following specifications:

Goal: {goal}
Weekly Hours: {weekly_hours}
Fitness Level: {fitness_level}{preferences_text}{strava_text}

Requirements:
- Create exactly 4 weeks of training
- Each week should have 7 days (Monday through Sunday)
- Distribute {weekly_hours} hours across the week appropriately
- Include rest days and recovery
- Use proper training zones and FTP percentages
- Include variety in workout types
- Personalize based on the user's Strava data when available

Workout Types:
- RECOVERY: Easy rides, <65% FTP
- ENDURANCE: Steady rides, 65-85% FTP  
- THRESHOLD: Tempo work, 91-105% FTP
- VO2MAX: High intensity intervals, 106-120% FTP
- CROSS_TRAINING: Strength, yoga, etc.
- REST: Complete rest days

Return ONLY a valid JSON object with this exact structure:
{{
  "weeks": [
    {{
      "week_start_date": "YYYY-MM-DD",
      "workouts": {{
        "monday": {{
          "id": "unique_id",
          "title": "Workout Title",
          "description": "Brief description",
          "duration_minutes": 60,
          "workout_type": "RECOVERY|ENDURANCE|THRESHOLD|VO2MAX|CROSS_TRAINING|REST",
          "ftp_percentage_min": 60,
          "ftp_percentage_max": 70,
          "details": "Detailed workout description"
        }},
        "tuesday": {{ ... }},
        "wednesday": {{ ... }},
        "thursday": {{ ... }},
        "friday": {{ ... }},
        "saturday": {{ ... }},
        "sunday": {{ ... }}
      }}
    }}
  ]
}}

Ensure the JSON is valid and complete. Start the first week from the current date.
"""
        return prompt

    def _parse_openai_response(self, response: str) -> Dict[str, Any]:
        """Parse the OpenAI response into structured plan data"""
        
        # Try to extract JSON from the response
        try:
            # Look for JSON in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[start_idx:end_idx]
            plan_data = json.loads(json_str)
            
            # Validate the structure
            if 'weeks' not in plan_data:
                raise ValueError("Invalid plan structure")
            
            # Process each week to ensure proper formatting
            for week in plan_data['weeks']:
                if 'workouts' in week:
                    for day, workout in week['workouts'].items():
                        # Ensure workout has required fields
                        if 'id' not in workout:
                            workout['id'] = str(uuid.uuid4())
                        if 'completed' not in workout:
                            workout['completed'] = False
            
            return plan_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in response: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing response: {e}")

    def _generate_fallback_plan(self, goal: str, weekly_hours: int) -> Dict[str, Any]:
        """Generate a fallback plan if OpenAI fails"""
        
        # Calculate daily distribution
        daily_hours = weekly_hours / 6  # 6 days of training, 1 rest day
        daily_minutes = int(daily_hours * 60)
        
        # Create a simple 4-week plan
        weeks = []
        current_date = datetime.now().date()
        
        for week_num in range(4):
            week_start = current_date + timedelta(weeks=week_num)
            week_workouts = {
                "monday": {
                    "id": str(uuid.uuid4()),
                    "title": "Recovery Ride",
                    "description": "Easy ride to start the week",
                    "duration_minutes": daily_minutes,
                    "workout_type": "RECOVERY",
                    "ftp_percentage_min": 50,
                    "ftp_percentage_max": 65,
                    "details": "Easy ride in Zone 1, <65% FTP to promote recovery.",
                    "completed": False
                },
                "tuesday": {
                    "id": str(uuid.uuid4()),
                    "title": "Endurance Ride",
                    "description": "Steady pace to build aerobic capacity",
                    "duration_minutes": daily_minutes,
                    "workout_type": "ENDURANCE",
                    "ftp_percentage_min": 65,
                    "ftp_percentage_max": 85,
                    "details": "Steady ride in Zone 2, 65-75% FTP to build aerobic capacity.",
                    "completed": False
                },
                "wednesday": {
                    "id": str(uuid.uuid4()),
                    "title": "Threshold Intervals",
                    "description": "Tempo work to improve threshold",
                    "duration_minutes": daily_minutes,
                    "workout_type": "THRESHOLD",
                    "ftp_percentage_min": 91,
                    "ftp_percentage_max": 105,
                    "details": "Warm-up followed by 4 x 8 min intervals in Zone 4, 91-105% FTP with 4 min recovery between.",
                    "completed": False
                },
                "thursday": {
                    "id": str(uuid.uuid4()),
                    "title": "Recovery Ride",
                    "description": "Easy recovery ride",
                    "duration_minutes": daily_minutes // 2,
                    "workout_type": "RECOVERY",
                    "ftp_percentage_min": 50,
                    "ftp_percentage_max": 65,
                    "details": "Easy recovery ride to promote recovery.",
                    "completed": False
                },
                "friday": {
                    "id": str(uuid.uuid4()),
                    "title": "Endurance Ride",
                    "description": "Steady endurance work",
                    "duration_minutes": daily_minutes,
                    "workout_type": "ENDURANCE",
                    "ftp_percentage_min": 65,
                    "ftp_percentage_max": 85,
                    "details": "Steady ride in Zone 2, 65-75% FTP to build aerobic capacity.",
                    "completed": False
                },
                "saturday": {
                    "id": str(uuid.uuid4()),
                    "title": "VO2max Intervals",
                    "description": "High intensity intervals",
                    "duration_minutes": daily_minutes,
                    "workout_type": "VO2MAX",
                    "ftp_percentage_min": 106,
                    "ftp_percentage_max": 120,
                    "details": "Warm-up followed by 5 x 3 min intervals in Zone 5, 106-120% FTP with 3 min recovery between.",
                    "completed": False
                },
                "sunday": {
                    "id": str(uuid.uuid4()),
                    "title": "Rest Day",
                    "description": "Complete rest",
                    "duration_minutes": 0,
                    "workout_type": "REST",
                    "ftp_percentage_min": None,
                    "ftp_percentage_max": None,
                    "details": "Complete rest to allow for recovery and adaptation.",
                    "completed": False
                }
            }
            
            weeks.append({
                "week_start_date": week_start.isoformat(),
                "workouts": week_workouts
            })
        
        return {"weeks": weeks}


training_plan_generator = TrainingPlanGenerator()