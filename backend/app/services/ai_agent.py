"""
AI Agent Framework for Reroute

This module provides the core AI agent functionality that allows the chat AI
to take actions on behalf of users, such as modifying training plans and 
generating routes.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.database import uuid_to_db_format
from app.models.training import TrainingPlan
from app.models.user import Profile, User
from app.schemas.training import WorkoutType

logger = logging.getLogger(__name__)


@dataclass
class AgentTool:
    """Represents a tool/function that the AI agent can use."""

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for parameters
    function: Callable  # The actual function to execute


class AIAgent:
    """AI Agent that can execute tools based on OpenAI function calling."""

    def __init__(self):
        self.tools: Dict[str, AgentTool] = {}
        self._register_core_tools()

    def register_tool(self, tool: AgentTool):
        """Register a new tool with the agent."""
        self.tools[tool.name] = tool
        logger.info(f"Registered agent tool: {tool.name}")

    def _register_core_tools(self):
        """Register the core set of tools for training plan management."""

        # Training Plan Tools
        self.register_tool(
            AgentTool(
                name="update_training_plan",
                description="Update specific fields in the user's training plan, including day-specific workouts (monday, tuesday, etc.)",
                parameters={
                    "type": "object",
                    "properties": {
                        "field": {
                            "type": "string",
                            "description": "The field to update (e.g., 'monday', 'tuesday', 'weekly_training_hours', 'goal')",
                        },
                        "value": {
                            "type": "string",
                            "description": "The new value for the field",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Explanation for why this change is being made",
                        },
                    },
                    "required": ["field", "value", "reason"],
                },
                function=self._update_training_plan,
            )
        )

        self.register_tool(
            AgentTool(
                name="update_training_plan_dates",
                description="Update the training plan to use current dates instead of old dates",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                function=self.update_training_plan_dates,
            )
        )

        self.register_tool(
            AgentTool(
                name="add_training_block",
                description="Add a new training block or workout to the user's plan",
                parameters={
                    "type": "object",
                    "properties": {
                        "block_type": {
                            "type": "string",
                            "enum": ["workout", "rest_day", "training_phase"],
                            "description": "Type of training block to add",
                        },
                        "details": {
                            "type": "object",
                            "description": "Details of the training block (duration, intensity, etc.)",
                        },
                        "schedule": {
                            "type": "string",
                            "description": "When this block should be scheduled (e.g., 'Monday', 'Week 3')",
                        },
                    },
                    "required": ["block_type", "details"],
                },
                function=self._add_training_block,
            )
        )

        self.register_tool(
            AgentTool(
                name="analyze_training_progress",
                description="Analyze the user's training progress and suggest modifications",
                parameters={
                    "type": "object",
                    "properties": {
                        "analysis_type": {
                            "type": "string",
                            "enum": ["weekly", "monthly", "performance_trend"],
                            "description": "Type of analysis to perform",
                        },
                        "metrics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific metrics to analyze (power, cadence, distance, etc.)",
                        },
                    },
                    "required": ["analysis_type"],
                },
                function=self._analyze_training_progress,
            )
        )

        # Phase 2: Advanced Training Plan Tools
        self.register_tool(
            AgentTool(
                name="modify_workout_intensity",
                description="Modify the intensity of specific workouts in the training plan",
                parameters={
                    "type": "object",
                    "properties": {
                        "day": {
                            "type": "string",
                            "enum": [
                                "monday",
                                "tuesday",
                                "wednesday",
                                "thursday",
                                "friday",
                                "saturday",
                                "sunday",
                            ],
                            "description": "Day of the week to modify",
                        },
                        "week_number": {
                            "type": "integer",
                            "description": "Week number to modify (1-based index)",
                        },
                        "intensity_adjustment": {
                            "type": "string",
                            "enum": ["increase", "decrease", "maintain"],
                            "description": "How to adjust the workout intensity",
                        },
                        "adjustment_percentage": {
                            "type": "integer",
                            "description": "Percentage to adjust intensity by (5-50%)",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for the intensity modification",
                        },
                    },
                    "required": ["day", "intensity_adjustment", "reason"],
                },
                function=self._modify_workout_intensity,
            )
        )

        self.register_tool(
            AgentTool(
                name="schedule_recovery_week",
                description="Schedule a recovery week in the training plan",
                parameters={
                    "type": "object",
                    "properties": {
                        "week_number": {
                            "type": "integer",
                            "description": "Week number to convert to recovery (1-based index)",
                        },
                        "recovery_level": {
                            "type": "string",
                            "enum": ["light", "moderate", "complete"],
                            "description": "Level of recovery for the week",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for scheduling recovery week",
                        },
                    },
                    "required": ["recovery_level", "reason"],
                },
                function=self._schedule_recovery_week,
            )
        )

        self.register_tool(
            AgentTool(
                name="adjust_training_volume",
                description="Adjust the overall training volume for specific weeks or the entire plan",
                parameters={
                    "type": "object",
                    "properties": {
                        "adjustment_type": {
                            "type": "string",
                            "enum": ["increase", "decrease", "taper"],
                            "description": "Type of volume adjustment",
                        },
                        "target_weeks": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Specific week numbers to adjust (empty for all weeks)",
                        },
                        "volume_change_percent": {
                            "type": "integer",
                            "description": "Percentage to change volume by (5-50%)",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for volume adjustment",
                        },
                    },
                    "required": ["adjustment_type", "volume_change_percent", "reason"],
                },
                function=self._adjust_training_volume,
            )
        )

        self.register_tool(
            AgentTool(
                name="add_periodization_phase",
                description="Add or modify periodization phases in the training plan",
                parameters={
                    "type": "object",
                    "properties": {
                        "phase_name": {
                            "type": "string",
                            "enum": [
                                "base",
                                "build",
                                "peak",
                                "recovery",
                                "preparation",
                            ],
                            "description": "Name of the training phase",
                        },
                        "start_week": {
                            "type": "integer",
                            "description": "Week number when phase starts (1-based index)",
                        },
                        "duration_weeks": {
                            "type": "integer",
                            "description": "Duration of the phase in weeks",
                        },
                        "focus_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Primary focus areas for this phase (endurance, power, recovery, etc.)",
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of what this phase aims to achieve",
                        },
                    },
                    "required": [
                        "phase_name",
                        "start_week",
                        "duration_weeks",
                        "focus_areas",
                    ],
                },
                function=self._add_periodization_phase,
            )
        )

        # Route Generation Tools
        self.register_tool(
            AgentTool(
                name="generate_workout_route",
                description=(
                    "Generate a contextual training route for a specific workout type. "
                    "The route terrain is matched to the workout: flat uninterrupted "
                    "roads for threshold/VO2max intervals, rolling hills for cross-training, "
                    "and paved roads with appropriate gradient for endurance and recovery. "
                    "Requires the user to have a home location set in their profile."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "workout_type": {
                            "type": "string",
                            "enum": ["endurance", "threshold", "vo2max", "recovery", "cross_training"],
                            "description": "Type of workout the route should support",
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Duration of the workout in minutes (used to size the route)",
                        },
                        "difficulty": {
                            "type": "string",
                            "enum": ["easy", "moderate", "hard"],
                            "description": "Scales interval segment length requirements. Default: moderate.",
                        },
                    },
                    "required": ["workout_type", "duration_minutes"],
                },
                function=self._generate_workout_route,
            )
        )

        self.register_tool(
            AgentTool(
                name="simulate_race_route",
                description=(
                    "Generate a local training route that mimics the terrain profile of a "
                    "specific professional cycling race. The agent researches the race's "
                    "elevation, gradient, surface type, and punchiness, then generates a "
                    "route near the user's home that replicates those characteristics."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "race_name": {
                            "type": "string",
                            "description": (
                                "Name of the cycling race to simulate. "
                                "Examples: 'Paris-Roubaix', 'Tour de France Stage 1', "
                                "'Strade Bianche', 'Alpe d Huez stage'."
                            ),
                        },
                        "target_distance_km": {
                            "type": "number",
                            "description": (
                                "Scale the simulation to this distance (km). "
                                "The ascent-per-km ratio is preserved. "
                                "If omitted, defaults to a practical local training distance."
                            ),
                        },
                    },
                    "required": ["race_name"],
                },
                function=self._simulate_race_route,
            )
        )

        # Route Management Tools
        self.register_tool(
            AgentTool(
                name="list_routes",
                description="List the user's saved routes with name, distance, and type.",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of routes to return (default 5, max 20)",
                        }
                    },
                    "required": [],
                },
                function=self._list_routes,
            )
        )

        self.register_tool(
            AgentTool(
                name="generate_route",
                description=(
                    "Generate a new loop cycling route near the user's home location. "
                    "Use this when the user asks to create a route of a specific distance or type."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "distance_km": {
                            "type": "number",
                            "description": "Target distance for the loop route in kilometres.",
                        },
                        "profile": {
                            "type": "string",
                            "enum": ["bike", "gravel", "mtb"],
                            "description": "Cycling profile. Default: bike (road).",
                        },
                    },
                    "required": ["distance_km"],
                },
                function=self._generate_route,
            )
        )

        self.register_tool(
            AgentTool(
                name="delete_route",
                description="Delete one of the user's saved routes by name or ID.",
                parameters={
                    "type": "object",
                    "properties": {
                        "route_name_or_id": {
                            "type": "string",
                            "description": "The name or ID of the route to delete.",
                        }
                    },
                    "required": ["route_name_or_id"],
                },
                function=self._delete_route,
            )
        )

        self.register_tool(
            AgentTool(
                name="rename_route",
                description="Rename one of the user's saved routes.",
                parameters={
                    "type": "object",
                    "properties": {
                        "route_name_or_id": {
                            "type": "string",
                            "description": "The current name or ID of the route to rename.",
                        },
                        "new_name": {
                            "type": "string",
                            "description": "The new name for the route.",
                        },
                    },
                    "required": ["route_name_or_id", "new_name"],
                },
                function=self._rename_route,
            )
        )

        # Profile Tools
        self.register_tool(
            AgentTool(
                name="get_profile",
                description="Read the user's current profile settings (fitness level, goals, weight, equipment, etc.).",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                function=self._get_profile,
            )
        )

        self.register_tool(
            AgentTool(
                name="update_profile",
                description=(
                    "Update one or more fields in the user's profile. "
                    "Only pass the fields you want to change."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "weight_lbs": {
                            "type": "number",
                            "description": "User's weight in pounds",
                        },
                        "fitness_level": {
                            "type": "string",
                            "enum": ["beginner", "intermediate", "advanced", "elite"],
                            "description": "Current fitness level",
                        },
                        "weekly_training_hours": {
                            "type": "number",
                            "description": "Target weekly training hours",
                        },
                        "primary_goals": {
                            "type": "string",
                            "description": "User's primary training goals (free text)",
                        },
                        "equipment_available": {
                            "type": "string",
                            "description": "Equipment description (free text)",
                        },
                        "preferred_training_days": {
                            "type": "string",
                            "description": "Preferred days to train, e.g. 'Monday, Wednesday, Saturday'",
                        },
                    },
                    "required": [],
                },
                function=self._update_profile,
            )
        )

        # Training Plan Generation & Workout Update Tools
        self.register_tool(
            AgentTool(
                name="generate_training_plan",
                description=(
                    "Generate a completely new training plan for the user. "
                    "Use this when the user asks to create or start a new training plan. "
                    "This replaces any currently active plan."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "goal": {
                            "type": "string",
                            "description": "Training goal, e.g. 'Build base fitness', 'Prepare for a sportive', 'Improve FTP'",
                        },
                        "weekly_hours": {
                            "type": "number",
                            "description": "Target weekly training hours (e.g. 8)",
                        },
                        "fitness_level": {
                            "type": "string",
                            "enum": ["beginner", "intermediate", "advanced"],
                            "description": "Current fitness level",
                        },
                    },
                    "required": ["goal", "weekly_hours", "fitness_level"],
                },
                function=self._generate_training_plan,
            )
        )

        self.register_tool(
            AgentTool(
                name="update_workout",
                description=(
                    "Update a specific day's workout in the user's active training plan. "
                    "Use this to change the workout type, title, duration, or description for a specific day."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "day": {
                            "type": "string",
                            "enum": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                            "description": "Day of the week to update",
                        },
                        "title": {
                            "type": "string",
                            "description": "Workout title, e.g. 'Threshold Intervals'",
                        },
                        "workout_type": {
                            "type": "string",
                            "enum": ["endurance", "threshold", "vo2max", "recovery", "cross_training", "rest"],
                            "description": "Workout type",
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Duration in minutes",
                        },
                        "description": {
                            "type": "string",
                            "description": "Workout description or instructions",
                        },
                        "week_number": {
                            "type": "integer",
                            "description": "1-based week number to update. Defaults to week 1 (current week).",
                        },
                    },
                    "required": ["day"],
                },
                function=self._update_workout_structured,
            )
        )

        # Strava Tools
        self.register_tool(
            AgentTool(
                name="get_strava_activities",
                description=(
                    "Fetch the user's recent Strava activities with key metrics "
                    "(distance, speed, power, heart rate). Use this when the user "
                    "asks about their recent rides or activity data."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of recent activities to fetch (default 5, max 20)",
                        }
                    },
                    "required": [],
                },
                function=self._get_strava_activities,
            )
        )

        self.register_tool(
            AgentTool(
                name="trigger_strava_sync",
                description=(
                    "Trigger a Strava data sync to pull in the user's latest activities. "
                    "Use this when the user's data seems out of date or they ask to sync."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                function=self._trigger_strava_sync,
            )
        )

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Convert agent tools to OpenAI function calling format."""
        openai_tools = []
        for tool in self.tools.values():
            openai_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
            )
        return openai_tools

    def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any], db: Session, user: User
    ) -> Dict[str, Any]:
        """Execute a tool with the given parameters."""
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "result": None,
            }

        tool = self.tools[tool_name]
        try:
            logger.info(f"Executing tool {tool_name} with parameters: {parameters}")
            result = tool.function(db, user, **parameters)
            return {"success": True, "error": None, "result": result}
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {"success": False, "error": str(e), "result": None}

    # Tool Implementation Methods

    def _get_or_create_user_training_plan(
        self, db: Session, user: User
    ) -> TrainingPlan:
        """Get the user's training plan using the same logic as the UI (active plan or most recent)."""
        user_id = uuid_to_db_format(user.id)
        logger.info(f"AI Agent: Getting training plan for user {user.id}")

        # First try to get active plan (most recently updated one if multiple active)
        plan = (
            db.query(TrainingPlan)
            .filter(TrainingPlan.user_id == user_id, TrainingPlan.is_active == True)
            .order_by(TrainingPlan.created_at.desc())  # Get newest active plan
            .first()
        )
        if plan:
            logger.info(f"AI Agent: Found active plan {plan.id}")
            return plan

        # Fallback to most recent plan if no active plan
        plan = (
            db.query(TrainingPlan)
            .filter(TrainingPlan.user_id == user_id)
            .order_by(TrainingPlan.updated_at.desc())
            .first()
        )
        if plan:
            logger.info(f"AI Agent: Found most recent plan {plan.id} (not active)")
            return plan

        # Create new plan only if user has no plans at all
        logger.info(f"AI Agent: Creating new plan for user {user.id}")
        plan = TrainingPlan(user_id=user_id, plan_data={}, is_active=True)
        db.add(plan)
        db.flush()  # Ensure the plan gets an ID
        logger.info(f"AI Agent: Created new plan {plan.id}")
        return plan

    def _update_training_plan(
        self, db: Session, user: User, field: str, value: str, reason: str
    ) -> Dict[str, Any]:
        """Update a specific field in the user's training plan."""
        try:
            logger.info(
                f"AI Agent: Updating training plan field '{field}' to '{value}' for user {user.id}"
            )

            # Get or create training plan using UI logic
            plan = self._get_or_create_user_training_plan(db, user)
            logger.debug(f"AI Agent: Found/created plan {plan.id}, is_active={plan.is_active}")

            # Initialize plan_data if needed
            if plan.plan_data is None:
                plan.plan_data = {}

            # Convert value to appropriate type
            processed_value = self._process_value(value)

            # Check if this is a day-specific update (monday, tuesday, etc.)
            days_of_week = [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]

            if field.lower() in days_of_week:
                # Handle day-specific workout updates
                old_value = self._update_workout_for_day(
                    plan, field.lower(), processed_value, reason
                )
            else:
                # Handle general plan field updates
                old_value = plan.plan_data.get(field, "Not set")
                plan.plan_data[field] = processed_value

            plan.updated_at = datetime.utcnow()

            # Log the change
            if "change_log" not in plan.plan_data:
                plan.plan_data["change_log"] = []

            plan.plan_data["change_log"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "field": field,
                    "old_value": old_value,
                    "new_value": processed_value,
                    "reason": reason,
                    "changed_by": "AI Agent",
                }
            )

            # Flush and commit to ensure changes are immediately visible
            db.flush()
            db.commit()
            db.refresh(plan)  # Refresh to get updated data

            logger.info(
                f"AI Agent: Successfully updated plan {plan.id}, field '{field}' = '{processed_value}'"
            )

            return {
                "action": "update_training_plan",
                "field": field,
                "old_value": old_value,
                "new_value": processed_value,
                "reason": reason,
                "message": f"Successfully updated {field} from '{old_value}' to '{processed_value}'. Reason: {reason}",
                "action_type": "training_plan_updated",
                "action_title": "Training Plan Updated",
                "action_description": f"Updated {field}: '{old_value}' → '{processed_value}'",
                "action_nav_url": "/training",
            }

        except Exception as e:
            db.rollback()
            raise e

    def _update_workout_for_day(
        self, plan: TrainingPlan, day: str, workout_value: str, reason: str
    ) -> str:
        """Update a specific day's workout in the training plan structure."""
        import uuid

        # Initialize weeks if needed
        if "weeks" not in plan.plan_data:
            plan.plan_data["weeks"] = []

        # If no weeks exist, create a default week starting today
        if not plan.plan_data["weeks"]:
            from datetime import datetime, timedelta

            # Find the Monday of this week
            today = datetime.now()
            monday = today - timedelta(days=today.weekday())

            plan.plan_data["weeks"].append(
                {
                    "week_start_date": monday.strftime("%Y-%m-%d"),
                    "workouts": {
                        "monday": {
                            "id": str(uuid.uuid4()),
                            "title": "Rest Day",
                            "workout_type": "rest",
                            "duration_minutes": 0,
                            "description": "Rest day",
                            "completed": False,
                        },
                        "tuesday": {
                            "id": str(uuid.uuid4()),
                            "title": "Rest Day",
                            "workout_type": "rest",
                            "duration_minutes": 0,
                            "description": "Rest day",
                            "completed": False,
                        },
                        "wednesday": {
                            "id": str(uuid.uuid4()),
                            "title": "Rest Day",
                            "workout_type": "rest",
                            "duration_minutes": 0,
                            "description": "Rest day",
                            "completed": False,
                        },
                        "thursday": {
                            "id": str(uuid.uuid4()),
                            "title": "Rest Day",
                            "workout_type": "rest",
                            "duration_minutes": 0,
                            "description": "Rest day",
                            "completed": False,
                        },
                        "friday": {
                            "id": str(uuid.uuid4()),
                            "title": "Rest Day",
                            "workout_type": "rest",
                            "duration_minutes": 0,
                            "description": "Rest day",
                            "completed": False,
                        },
                        "saturday": {
                            "id": str(uuid.uuid4()),
                            "title": "Rest Day",
                            "workout_type": "rest",
                            "duration_minutes": 0,
                            "description": "Rest day",
                            "completed": False,
                        },
                        "sunday": {
                            "id": str(uuid.uuid4()),
                            "title": "Rest Day",
                            "workout_type": "rest",
                            "duration_minutes": 0,
                            "description": "Rest day",
                            "completed": False,
                        },
                    },
                }
            )

        # Get the first week (for simplicity, update the current/first week)
        week = plan.plan_data["weeks"][0]
        old_workout = week["workouts"][day]
        old_value = old_workout.get("title", "Rest Day")

        # Update the workout
        print(
            f"🔥 WORKOUT UPDATE DEBUG: Updating {day} workout with value '{workout_value}'"
        )
        print(
            f"🔥 WORKOUT UPDATE DEBUG: Old workout title: '{old_workout.get('title', 'Unknown')}'"
        )

        if workout_value.lower() in ["strength training", "strength"]:
            print(f"🔥 WORKOUT UPDATE DEBUG: Matched strength training pattern")
            week["workouts"][day].update(
                {
                    "title": "Strength Training",
                    "workout_type": "cross_training",
                    "duration_minutes": 60,
                    "description": f"Strength training session focusing on functional movement and cycling-specific exercises. {reason}",
                }
            )
            print(
                f"🔥 WORKOUT UPDATE DEBUG: Updated {day} title to: '{week['workouts'][day]['title']}')"
            )
        elif workout_value.lower() in ["endurance", "endurance ride"]:
            week["workouts"][day].update(
                {
                    "title": "Endurance Ride",
                    "workout_type": "endurance",
                    "duration_minutes": 90,
                    "description": f"Steady-state endurance ride to build aerobic capacity. {reason}",
                }
            )
        elif workout_value.lower() in ["rest", "rest day"]:
            week["workouts"][day].update(
                {
                    "title": "Rest Day",
                    "workout_type": "rest",
                    "duration_minutes": 0,
                    "description": f"Recovery day for optimal training adaptation. {reason}",
                }
            )
        elif workout_value.lower() in ["threshold", "threshold ride"]:
            week["workouts"][day].update(
                {
                    "title": "Threshold Ride",
                    "workout_type": "threshold",
                    "duration_minutes": 75,
                    "description": f"Lactate threshold intervals to improve sustainable power. {reason}",
                }
            )
        elif workout_value.lower() in ["vo2max", "vo2 max", "intervals"]:
            week["workouts"][day].update(
                {
                    "title": "VO2max Intervals",
                    "workout_type": "vo2max",
                    "duration_minutes": 60,
                    "description": f"High-intensity intervals to improve maximum oxygen uptake. {reason}",
                }
            )
        else:
            # Generic workout update
            week["workouts"][day].update(
                {
                    "title": workout_value,
                    "workout_type": "endurance",
                    "duration_minutes": 60,
                    "description": f"Custom workout: {workout_value}. {reason}",
                }
            )

        return old_value

    def _add_training_block(
        self,
        db: Session,
        user: User,
        block_type: str,
        details: Dict[str, Any],
        schedule: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a new training block to the user's plan."""
        try:
            # Get or create training plan using UI logic
            plan = self._get_or_create_user_training_plan(db, user)

            if plan.plan_data is None:
                plan.plan_data = {}

            # Initialize training blocks if needed
            if "training_blocks" not in plan.plan_data:
                plan.plan_data["training_blocks"] = []

            # Create new training block
            new_block = {
                "id": len(plan.plan_data["training_blocks"]) + 1,
                "type": block_type,
                "details": details,
                "schedule": schedule,
                "created_at": datetime.utcnow().isoformat(),
                "created_by": "AI Agent",
            }

            plan.plan_data["training_blocks"].append(new_block)
            plan.updated_at = datetime.utcnow()

            db.commit()

            return {
                "action": "add_training_block",
                "block": new_block,
                "message": f"Successfully added {block_type} to your training plan",
            }

        except Exception as e:
            db.rollback()
            raise e

    def _analyze_training_progress(
        self,
        db: Session,
        user: User,
        analysis_type: str,
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Analyze training progress and return insights using real Strava data."""
        try:
            from app.models.user import Profile
            from app.models.strava import StravaActivity
            import requests
            from datetime import datetime, timedelta

            # Get user's profile and Strava connection
            profile = db.query(Profile).filter(Profile.id == user.id).first()

            if not profile or not profile.strava_access_token:
                return {
                    "action": "analyze_training_progress",
                    "analysis_type": analysis_type,
                    "error": "Strava not connected",
                    "insights": [
                        "Connect your Strava account to get personalized training analysis"
                    ],
                    "recommendations": ["Connect to Strava in your profile settings"],
                    "message": "Unable to analyze progress - Strava account not connected",
                }

            # Get recent activities from Strava API
            activities_url = "https://www.strava.com/api/v3/athlete/activities"
            headers = {"Authorization": f"Bearer {profile.strava_access_token}"}

            # Determine time range based on analysis type
            now = datetime.now()
            if analysis_type == "weekly":
                after_date = now - timedelta(weeks=4)  # Last 4 weeks
                per_page = 30
            elif analysis_type == "monthly":
                after_date = now - timedelta(weeks=12)  # Last 3 months
                per_page = 50
            else:  # performance_trend
                after_date = now - timedelta(weeks=8)  # Last 2 months
                per_page = 40

            params = {"per_page": per_page, "after": int(after_date.timestamp())}

            response = requests.get(activities_url, headers=headers, params=params)

            if response.status_code != 200:
                return {
                    "action": "analyze_training_progress",
                    "analysis_type": analysis_type,
                    "error": "Failed to fetch Strava activities",
                    "insights": ["Unable to retrieve recent activity data"],
                    "recommendations": ["Check your Strava connection and try again"],
                    "message": "Analysis failed - could not access Strava data",
                }

            activities = response.json()

            if not activities:
                return {
                    "action": "analyze_training_progress",
                    "analysis_type": analysis_type,
                    "insights": [
                        "No recent activities found in the selected time period"
                    ],
                    "recommendations": [
                        "Log some activities on Strava to get training analysis"
                    ],
                    "message": "No recent activities to analyze",
                }

            # Filter for cycling activities
            cycling_activities = [
                act for act in activities if act.get("type") in ["Ride", "VirtualRide"]
            ]

            if not cycling_activities:
                return {
                    "action": "analyze_training_progress",
                    "analysis_type": analysis_type,
                    "insights": [
                        "No cycling activities found in the selected time period"
                    ],
                    "recommendations": [
                        "Log some cycling activities to get training analysis"
                    ],
                    "message": "Connect more cycling activities to get insights",
                }

            # Analyze the data
            analysis_results = self._perform_strava_analysis(
                cycling_activities,
                analysis_type,
                metrics or ["power", "distance", "heartrate"],
            )

            return {
                "action": "analyze_training_progress",
                "analysis_type": analysis_type,
                "metrics": metrics or ["power", "distance", "heartrate"],
                "activities_analyzed": len(cycling_activities),
                "insights": analysis_results["insights"],
                "recommendations": analysis_results["recommendations"],
                "data_summary": analysis_results["summary"],
                "message": f"Analyzed {len(cycling_activities)} cycling activities for {analysis_type} trends",
            }

        except Exception as e:
            logger.error(f"Error in analyze_training_progress: {str(e)}")
            return {
                "action": "analyze_training_progress",
                "analysis_type": analysis_type,
                "error": str(e),
                "insights": ["Unable to complete analysis due to an error"],
                "recommendations": ["Try again later or check your Strava connection"],
                "message": "Analysis failed due to technical error",
            }

    def _perform_strava_analysis(
        self, activities: List[Dict], analysis_type: str, metrics: List[str]
    ) -> Dict[str, Any]:
        """Perform detailed analysis on Strava activities."""
        from statistics import mean, median
        from datetime import datetime, timedelta

        # Calculate basic metrics
        total_distance = (
            sum(act.get("distance", 0) for act in activities) / 1000
        )  # Convert to km
        total_time = (
            sum(act.get("moving_time", 0) for act in activities) / 3600
        )  # Convert to hours
        total_elevation = sum(act.get("total_elevation_gain", 0) for act in activities)

        # Calculate averages for activities with data
        avg_speeds = [
            act.get("average_speed", 0) * 3.6
            for act in activities
            if act.get("average_speed")
        ]  # Convert to km/h
        avg_powers = [
            act.get("average_watts") for act in activities if act.get("average_watts")
        ]
        avg_heartrates = [
            act.get("average_heartrate")
            for act in activities
            if act.get("average_heartrate")
        ]

        # Time-based analysis
        activity_dates = [
            datetime.fromisoformat(act.get("start_date", "").replace("Z", "+00:00"))
            for act in activities
        ]
        activity_dates.sort()

        # Weekly consistency
        if activity_dates:
            date_range = (activity_dates[-1] - activity_dates[0]).days
            weeks_covered = max(1, date_range / 7)
            activities_per_week = len(activities) / weeks_covered
        else:
            activities_per_week = 0
            weeks_covered = 1

        # Generate insights based on analysis type
        insights = []
        recommendations = []

        if analysis_type == "weekly":
            insights.append(
                f"You've completed {len(activities)} cycling activities in the last 4 weeks"
            )
            insights.append(
                f"Average {activities_per_week:.1f} rides per week with {total_distance:.1f}km total distance"
            )

            if activities_per_week < 2:
                recommendations.append(
                    "Consider increasing ride frequency for better consistency"
                )
            elif activities_per_week > 5:
                recommendations.append(
                    "Great consistency! Make sure to include recovery days"
                )

            if avg_powers:
                avg_power = mean(avg_powers)
                insights.append(
                    f"Average power output: {avg_power:.0f}W across recent rides"
                )
                if avg_power < 150:
                    recommendations.append(
                        "Focus on building base power through consistent training"
                    )
                elif avg_power > 250:
                    recommendations.append(
                        "Strong power numbers! Consider power-based interval training"
                    )

        elif analysis_type == "monthly":
            monthly_distance = total_distance
            insights.append(
                f"Monthly distance: {monthly_distance:.1f}km over {len(activities)} rides"
            )
            insights.append(f"Total elevation gained: {total_elevation:.0f}m")

            if monthly_distance < 200:
                recommendations.append(
                    "Consider gradually increasing monthly distance for endurance development"
                )
            elif monthly_distance > 800:
                recommendations.append(
                    "Impressive volume! Ensure adequate recovery between sessions"
                )

            if avg_heartrates:
                avg_hr = mean(avg_heartrates)
                insights.append(
                    f"Average heart rate: {avg_hr:.0f} bpm across activities"
                )
                recommendations.append(
                    "Monitor heart rate trends to track fitness improvements"
                )

        else:  # performance_trend
            if len(activities) >= 5:
                # Analyze trend in recent vs older activities
                recent_activities = activities[: len(activities) // 2]
                older_activities = activities[len(activities) // 2 :]

                recent_avg_speed = mean(
                    [
                        act.get("average_speed", 0) * 3.6
                        for act in recent_activities
                        if act.get("average_speed")
                    ]
                )
                older_avg_speed = mean(
                    [
                        act.get("average_speed", 0) * 3.6
                        for act in older_activities
                        if act.get("average_speed")
                    ]
                )

                if recent_avg_speed > older_avg_speed * 1.05:
                    insights.append(
                        "Performance trending upward - your average speed has improved!"
                    )
                    recommendations.append(
                        "Continue current training approach - it's working well"
                    )
                elif recent_avg_speed < older_avg_speed * 0.95:
                    insights.append(
                        "Performance may be plateauing or declining slightly"
                    )
                    recommendations.append(
                        "Consider adding variety or increasing training intensity"
                    )
                else:
                    insights.append(
                        "Performance is stable - maintaining consistent output"
                    )
                    recommendations.append(
                        "Good consistency! Consider progressive overload for improvement"
                    )

                if avg_powers and len(avg_powers) >= 5:
                    recent_powers = [
                        act.get("average_watts")
                        for act in recent_activities
                        if act.get("average_watts")
                    ]
                    older_powers = [
                        act.get("average_watts")
                        for act in older_activities
                        if act.get("average_watts")
                    ]

                    if recent_powers and older_powers:
                        recent_power = mean(recent_powers)
                        older_power = mean(older_powers)
                        power_change = (
                            (recent_power - older_power) / older_power
                        ) * 100

                        insights.append(
                            f"Power output change: {power_change:+.1f}% over analyzed period"
                        )

                        if power_change > 5:
                            recommendations.append(
                                "Power is increasing well! Consider FTP testing"
                            )
                        elif power_change < -5:
                            recommendations.append(
                                "Power declining - check for overtraining or need for recovery"
                            )
            else:
                insights.append("Need more activities for meaningful trend analysis")
                recommendations.append(
                    "Complete more rides to get detailed performance insights"
                )

        # Add general recommendations based on data availability
        if not avg_powers:
            recommendations.append(
                "Consider using a power meter for more detailed training analysis"
            )
        if not avg_heartrates:
            recommendations.append(
                "Heart rate data would provide valuable training zone insights"
            )

        summary = {
            "total_activities": len(activities),
            "total_distance_km": round(total_distance, 1),
            "total_time_hours": round(total_time, 1),
            "total_elevation_m": round(total_elevation, 0),
            "avg_speed_kmh": round(mean(avg_speeds), 1) if avg_speeds else None,
            "avg_power_w": round(mean(avg_powers), 0) if avg_powers else None,
            "avg_heartrate_bpm": round(mean(avg_heartrates), 0)
            if avg_heartrates
            else None,
            "activities_per_week": round(activities_per_week, 1),
        }

        return {
            "insights": insights,
            "recommendations": recommendations,
            "summary": summary,
        }

    def _generate_workout_route(
        self,
        db: Session,
        user: User,
        workout_type: str,
        duration_minutes: int,
        difficulty: str = "moderate",
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a contextual training route for a specific workout type.

        Uses WorkoutRoutePlanner to map the workout type and duration to a
        TerrainTarget, then calls route_generation_service.generate_route()
        with the user's home location as the start point.
        """
        # Lazy import to avoid circular dependencies at module load time
        from app.schemas.route import RouteGenerationParams
        from app.services.route_generator import route_generation_service
        from app.services.workout_route_planner import workout_route_planner

        try:
            # Validate and coerce workout_type to enum
            try:
                wt = WorkoutType(workout_type)
            except ValueError:
                valid = [w.value for w in WorkoutType if w != WorkoutType.REST]
                raise ValueError(
                    f"Unknown workout_type '{workout_type}'. Valid types: {valid}"
                )

            # Build TerrainTarget from workout context
            terrain_target = workout_route_planner.workout_to_terrain_target(
                workout_type=wt,
                duration_minutes=duration_minutes,
                difficulty=difficulty,
            )

            # Get user's home location for route start point
            profile = db.query(Profile).filter(Profile.id == user.id).first()
            start_lat = getattr(profile, "home_lat", None) if profile else None
            start_lng = getattr(profile, "home_lng", None) if profile else None

            if start_lat is None or start_lng is None:
                return {
                    "action": "generate_workout_route",
                    "success": False,
                    "message": (
                        "No home location set on your profile. "
                        "Please set your location in Profile settings, "
                        "then I can generate a route from your home."
                    ),
                    "terrain_target": terrain_target.dict(),
                }

            # Estimate target distance: speed × duration, capped at reasonable bounds
            avg_speed_kmh = 24.0  # conservative planning speed
            target_distance_km = round(
                min(max((duration_minutes / 60.0) * avg_speed_kmh, 5.0), 200.0), 1
            )

            route_params = RouteGenerationParams(
                start_lat=start_lat,
                start_lng=start_lng,
                profile="bike",
                route_type="road",
                distance_km=target_distance_km,
                is_loop=True,
                terrain_target=terrain_target,
            )

            result = route_generation_service.generate_route(
                params=route_params,
                user_id=str(user.id),
                db=db,
            )

            route = result["route"]
            return {
                "action": "generate_workout_route",
                "success": True,
                "route_id": str(route.id),
                "name": route.name,
                "distance_km": round(route.distance_m / 1000, 1),
                "elevation_gain_m": round(route.total_elevation_gain_m, 0),
                "estimated_time_min": round((route.estimated_time_s or 0) / 60),
                "workout_type": workout_type,
                "terrain_target": terrain_target.dict(),
                "message": (
                    f"Generated a {round(route.distance_m / 1000, 1)}km "
                    f"{workout_type} route from your home location."
                ),
                "action_type": "route_generated",
                "action_title": f"New Route: {route.name}",
                "action_description": f"{round(route.distance_m / 1000, 1)}km {workout_type} route",
                "action_nav_url": "/routes",
            }

        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"Workout route generation failed: {e}")
            db.rollback()
            raise

    def _simulate_race_route(
        self,
        db: Session,
        user: User,
        race_name: str,
        target_distance_km: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Generate a local training route that mimics a target race's terrain profile.

        Researches the race using LLM + optional Strava fallback, converts the result
        to a TerrainTarget, and calls route_generation_service.generate_route().
        """
        from app.schemas.route import RouteGenerationParams
        from app.services.route_generator import route_generation_service
        from app.services.terrain_research_agent import terrain_research_agent

        try:
            # Get user's home location for route start point
            profile = db.query(Profile).filter(Profile.id == user.id).first()
            start_lat = getattr(profile, "home_lat", None) if profile else None
            start_lng = getattr(profile, "home_lng", None) if profile else None

            if start_lat is None or start_lng is None:
                return {
                    "action": "simulate_race_route",
                    "success": False,
                    "message": (
                        "No home location set on your profile. "
                        "Please set your location in Profile settings, "
                        "then I can simulate the race near you."
                    ),
                }

            # Research the race and build a TerrainTarget
            terrain_target = terrain_research_agent.research_race(
                race_name=race_name,
                user_lat=start_lat,
                user_lng=start_lng,
                db=db,
                user_id=str(user.id),
                target_distance_km=target_distance_km,
            )

            # Determine route distance
            route_distance_km = target_distance_km or 40.0  # Default 40km simulation

            route_params = RouteGenerationParams(
                start_lat=start_lat,
                start_lng=start_lng,
                profile="bike",
                route_type="road",
                distance_km=route_distance_km,
                is_loop=True,
                terrain_target=terrain_target,
            )

            result = route_generation_service.generate_route(
                params=route_params,
                user_id=str(user.id),
                db=db,
            )

            route = result["route"]
            return {
                "action": "simulate_race_route",
                "success": True,
                "race_name": race_name,
                "route_id": str(route.id),
                "name": route.name,
                "distance_km": round(route.distance_m / 1000, 1),
                "elevation_gain_m": round(route.total_elevation_gain_m, 0),
                "estimated_time_min": round((route.estimated_time_s or 0) / 60),
                "terrain_target": terrain_target.dict(),
                "message": (
                    f"Generated a {round(route.distance_m / 1000, 1)}km route "
                    f"near your home that mimics the terrain profile of {race_name}."
                ),
                "action_type": "route_generated",
                "action_title": f"Race Sim: {race_name}",
                "action_description": f"{round(route.distance_m / 1000, 1)}km terrain simulation",
                "action_nav_url": "/routes",
            }

        except Exception as e:
            logger.error(f"Race simulation route generation failed: {e}")
            db.rollback()
            raise

    def _process_value(self, value: str) -> Any:
        """Process and convert string values to appropriate types."""
        # Try to convert to number
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Try to convert to boolean
        if value.lower() in ["true", "yes", "on"]:
            return True
        elif value.lower() in ["false", "no", "off"]:
            return False

        # Return as string
        return value

    # Phase 2: Advanced Training Plan Tool Implementations

    def _modify_workout_intensity(
        self,
        db: Session,
        user: User,
        day: str,
        intensity_adjustment: str,
        reason: str,
        week_number: Optional[int] = None,
        adjustment_percentage: int = 15,
    ) -> Dict[str, Any]:
        """Modify the intensity of specific workouts in the training plan."""
        try:
            plan = self._get_or_create_user_training_plan(db, user)

            if plan.plan_data is None:
                plan.plan_data = {}

            if "weeks" not in plan.plan_data or not plan.plan_data["weeks"]:
                return {"error": "No weeks found in training plan"}

            # Determine which weeks to modify
            target_weeks = []
            if week_number is not None:
                if 1 <= week_number <= len(plan.plan_data["weeks"]):
                    target_weeks = [week_number - 1]  # Convert to 0-based index
                else:
                    return {"error": f"Invalid week number: {week_number}"}
            else:
                # Apply to all weeks if no specific week provided
                target_weeks = list(range(len(plan.plan_data["weeks"])))

            modifications_made = []
            for week_idx in target_weeks:
                week = plan.plan_data["weeks"][week_idx]
                if "workouts" in week and day in week["workouts"]:
                    workout = week["workouts"][day]
                    old_duration = workout.get("duration_minutes", 0)

                    # Adjust intensity based on duration and FTP percentages
                    if intensity_adjustment == "increase":
                        new_duration = int(
                            old_duration * (1 + adjustment_percentage / 100)
                        )
                        if "ftp_percentage_min" in workout:
                            workout["ftp_percentage_min"] = min(
                                120, workout["ftp_percentage_min"] + 5
                            )
                        if "ftp_percentage_max" in workout:
                            workout["ftp_percentage_max"] = min(
                                130, workout["ftp_percentage_max"] + 5
                            )
                    elif intensity_adjustment == "decrease":
                        new_duration = int(
                            old_duration * (1 - adjustment_percentage / 100)
                        )
                        if "ftp_percentage_min" in workout:
                            workout["ftp_percentage_min"] = max(
                                50, workout["ftp_percentage_min"] - 5
                            )
                        if "ftp_percentage_max" in workout:
                            workout["ftp_percentage_max"] = max(
                                60, workout["ftp_percentage_max"] - 5
                            )
                    else:  # maintain
                        new_duration = old_duration

                    workout["duration_minutes"] = max(
                        15, new_duration
                    )  # Minimum 15 minutes
                    modifications_made.append(
                        {
                            "week": week_idx + 1,
                            "day": day,
                            "old_duration": old_duration,
                            "new_duration": workout["duration_minutes"],
                        }
                    )

            # Log the changes
            if "change_log" not in plan.plan_data:
                plan.plan_data["change_log"] = []

            plan.plan_data["change_log"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "modify_workout_intensity",
                    "details": {
                        "day": day,
                        "intensity_adjustment": intensity_adjustment,
                        "adjustment_percentage": adjustment_percentage,
                        "modifications": modifications_made,
                    },
                    "reason": reason,
                    "changed_by": "AI Agent",
                }
            )

            plan.updated_at = datetime.utcnow()
            db.commit()

            return {
                "action": "modify_workout_intensity",
                "modifications": modifications_made,
                "message": f"Successfully {intensity_adjustment}d intensity for {day} workouts. Reason: {reason}",
            }

        except Exception as e:
            db.rollback()
            raise e

    def _schedule_recovery_week(
        self,
        db: Session,
        user: User,
        recovery_level: str,
        reason: str,
        week_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Schedule a recovery week in the training plan."""
        try:
            plan = self._get_or_create_user_training_plan(db, user)

            if plan.plan_data is None:
                plan.plan_data = {}

            if "weeks" not in plan.plan_data or not plan.plan_data["weeks"]:
                return {"error": "No weeks found in training plan"}

            # Find next week to convert to recovery if not specified
            if week_number is None:
                week_number = len(plan.plan_data["weeks"]) // 4 + 1  # Every 4th week

            if not (1 <= week_number <= len(plan.plan_data["weeks"])):
                return {"error": f"Invalid week number: {week_number}"}

            week_idx = week_number - 1
            week = plan.plan_data["weeks"][week_idx]

            # Define recovery levels
            recovery_settings = {
                "light": {"duration_multiplier": 0.7, "intensity_reduction": 10},
                "moderate": {"duration_multiplier": 0.5, "intensity_reduction": 20},
                "complete": {"duration_multiplier": 0.3, "intensity_reduction": 30},
            }

            settings = recovery_settings[recovery_level]

            # Modify all workouts in the week
            if "workouts" in week:
                for day, workout in week["workouts"].items():
                    if workout.get("workout_type") != "rest":
                        # Reduce duration and intensity
                        workout["duration_minutes"] = int(
                            workout.get("duration_minutes", 60)
                            * settings["duration_multiplier"]
                        )

                        # Change workout type to recovery if it's high intensity
                        if workout.get("workout_type") in ["threshold", "vo2max"]:
                            workout["workout_type"] = "recovery"

                        # Reduce FTP percentages
                        if "ftp_percentage_min" in workout:
                            workout["ftp_percentage_min"] = max(
                                50,
                                workout["ftp_percentage_min"]
                                - settings["intensity_reduction"],
                            )
                        if "ftp_percentage_max" in workout:
                            workout["ftp_percentage_max"] = max(
                                65,
                                workout["ftp_percentage_max"]
                                - settings["intensity_reduction"],
                            )

            # Mark week as recovery week
            if "week_metadata" not in plan.plan_data:
                plan.plan_data["week_metadata"] = {}

            plan.plan_data["week_metadata"][str(week_number)] = {
                "type": "recovery",
                "level": recovery_level,
                "scheduled_by": "AI Agent",
                "reason": reason,
            }

            # Log the change
            if "change_log" not in plan.plan_data:
                plan.plan_data["change_log"] = []

            plan.plan_data["change_log"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "schedule_recovery_week",
                    "details": {
                        "week_number": week_number,
                        "recovery_level": recovery_level,
                    },
                    "reason": reason,
                    "changed_by": "AI Agent",
                }
            )

            plan.updated_at = datetime.utcnow()
            db.commit()

            return {
                "action": "schedule_recovery_week",
                "week_number": week_number,
                "recovery_level": recovery_level,
                "message": f"Successfully scheduled {recovery_level} recovery week for week {week_number}. Reason: {reason}",
            }

        except Exception as e:
            db.rollback()
            raise e

    def _adjust_training_volume(
        self,
        db: Session,
        user: User,
        adjustment_type: str,
        volume_change_percent: int,
        reason: str,
        target_weeks: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Adjust the overall training volume for specific weeks or the entire plan."""
        try:
            plan = self._get_or_create_user_training_plan(db, user)

            if plan.plan_data is None:
                plan.plan_data = {}

            if "weeks" not in plan.plan_data or not plan.plan_data["weeks"]:
                return {"error": "No weeks found in training plan"}

            # Determine which weeks to adjust
            if target_weeks is None:
                week_indices = list(range(len(plan.plan_data["weeks"])))
            else:
                week_indices = [
                    w - 1
                    for w in target_weeks
                    if 1 <= w <= len(plan.plan_data["weeks"])
                ]

            volume_multiplier = 1.0
            if adjustment_type == "increase":
                volume_multiplier = 1 + (volume_change_percent / 100)
            elif adjustment_type == "decrease":
                volume_multiplier = 1 - (volume_change_percent / 100)
            elif adjustment_type == "taper":
                # Taper reduces volume progressively
                volume_multiplier = 1 - (volume_change_percent / 100)

            adjustments_made = []
            for week_idx in week_indices:
                week = plan.plan_data["weeks"][week_idx]
                if "workouts" in week:
                    week_total_before = 0
                    week_total_after = 0

                    for day, workout in week["workouts"].items():
                        old_duration = workout.get("duration_minutes", 0)
                        week_total_before += old_duration

                        if workout.get("workout_type") != "rest":
                            new_duration = int(old_duration * volume_multiplier)
                            workout["duration_minutes"] = max(15, new_duration)
                            week_total_after += workout["duration_minutes"]
                        else:
                            week_total_after += old_duration

                    adjustments_made.append(
                        {
                            "week": week_idx + 1,
                            "total_minutes_before": week_total_before,
                            "total_minutes_after": week_total_after,
                            "change_percent": round(
                                (
                                    (week_total_after - week_total_before)
                                    / max(1, week_total_before)
                                )
                                * 100,
                                1,
                            ),
                        }
                    )

            # Log the change
            if "change_log" not in plan.plan_data:
                plan.plan_data["change_log"] = []

            plan.plan_data["change_log"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "adjust_training_volume",
                    "details": {
                        "adjustment_type": adjustment_type,
                        "volume_change_percent": volume_change_percent,
                        "target_weeks": target_weeks or "all",
                        "adjustments": adjustments_made,
                    },
                    "reason": reason,
                    "changed_by": "AI Agent",
                }
            )

            plan.updated_at = datetime.utcnow()
            db.commit()

            return {
                "action": "adjust_training_volume",
                "adjustment_type": adjustment_type,
                "adjustments": adjustments_made,
                "message": f"Successfully {adjustment_type}d training volume by {volume_change_percent}%. Reason: {reason}",
            }

        except Exception as e:
            db.rollback()
            raise e

    def _add_periodization_phase(
        self,
        db: Session,
        user: User,
        phase_name: str,
        start_week: int,
        duration_weeks: int,
        focus_areas: List[str],
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add or modify periodization phases in the training plan."""
        try:
            plan = self._get_or_create_user_training_plan(db, user)

            if plan.plan_data is None:
                plan.plan_data = {}

            # Initialize periodization structure
            if "periodization" not in plan.plan_data:
                plan.plan_data["periodization"] = {"phases": []}

            # Validate week range
            total_weeks = len(plan.plan_data.get("weeks", []))
            if start_week < 1 or start_week + duration_weeks - 1 > total_weeks:
                return {
                    "error": f"Phase weeks {start_week}-{start_week + duration_weeks - 1} exceed plan duration of {total_weeks} weeks"
                }

            # Create new phase
            new_phase = {
                "name": phase_name,
                "start_week": start_week,
                "end_week": start_week + duration_weeks - 1,
                "duration_weeks": duration_weeks,
                "focus_areas": focus_areas,
                "description": description
                or f"{phase_name.title()} phase focusing on {', '.join(focus_areas)}",
                "created_by": "AI Agent",
                "created_at": datetime.utcnow().isoformat(),
            }

            # Remove any overlapping phases
            existing_phases = plan.plan_data["periodization"]["phases"]
            non_overlapping_phases = []
            for phase in existing_phases:
                if not (
                    start_week <= phase["end_week"]
                    and phase["start_week"] <= start_week + duration_weeks - 1
                ):
                    non_overlapping_phases.append(phase)

            non_overlapping_phases.append(new_phase)
            plan.plan_data["periodization"]["phases"] = sorted(
                non_overlapping_phases, key=lambda p: p["start_week"]
            )

            # Apply phase-specific modifications to workouts
            phase_settings = {
                "base": {"endurance_focus": 0.7, "intensity_focus": 0.3},
                "build": {"endurance_focus": 0.5, "intensity_focus": 0.5},
                "peak": {"endurance_focus": 0.3, "intensity_focus": 0.7},
                "recovery": {"endurance_focus": 0.8, "intensity_focus": 0.2},
                "preparation": {"endurance_focus": 0.6, "intensity_focus": 0.4},
            }

            settings = phase_settings.get(
                phase_name, {"endurance_focus": 0.5, "intensity_focus": 0.5}
            )

            # Log the change
            if "change_log" not in plan.plan_data:
                plan.plan_data["change_log"] = []

            plan.plan_data["change_log"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "add_periodization_phase",
                    "details": new_phase,
                    "reason": f"Added {phase_name} phase to structure training progression",
                    "changed_by": "AI Agent",
                }
            )

            plan.updated_at = datetime.utcnow()
            db.commit()

            return {
                "action": "add_periodization_phase",
                "phase": new_phase,
                "message": f"Successfully added {phase_name} phase for weeks {start_week}-{start_week + duration_weeks - 1}",
            }

        except Exception as e:
            db.rollback()
            raise e

    def update_training_plan_dates(self, db: Session, user: User) -> Dict[str, Any]:
        """Update an existing training plan to use current dates."""
        try:
            plan = self._get_or_create_user_training_plan(db, user)

            if not plan.plan_data or "weeks" not in plan.plan_data:
                return {"error": "No training plan found or plan has no weeks"}

            # Calculate current week dates
            from datetime import datetime, timedelta

            today = datetime.now().date()
            current_monday = today - timedelta(days=today.weekday())

            # Update each week's start date
            updates_made = []
            for i, week in enumerate(plan.plan_data["weeks"]):
                old_date = week.get("week_start_date", "Unknown")
                new_date = (current_monday + timedelta(weeks=i)).strftime("%Y-%m-%d")
                week["week_start_date"] = new_date
                updates_made.append(f"Week {i+1}: {old_date} → {new_date}")

            plan.updated_at = datetime.utcnow()

            # Log the change
            if "change_log" not in plan.plan_data:
                plan.plan_data["change_log"] = []

            plan.plan_data["change_log"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "update_training_plan_dates",
                    "details": {"updates": updates_made},
                    "reason": "Updated training plan to use current dates",
                    "changed_by": "AI Agent",
                }
            )

            db.commit()

            return {
                "action": "update_training_plan_dates",
                "updates": updates_made,
                "message": f"Successfully updated {len(updates_made)} weeks to current dates",
            }

        except Exception as e:
            db.rollback()
            raise e

    # ── Route Management Tools ────────────────────────────────────────────────

    def _list_routes(
        self, db: Session, user: User, limit: int = 5
    ) -> Dict[str, Any]:
        """Return a summary of the user's saved routes."""
        from app.models.route import Route
        from app.core.database import uuid_to_db_format

        limit = min(max(1, limit), 20)
        routes = (
            db.query(Route)
            .filter(Route.user_id == uuid_to_db_format(user.id))
            .order_by(Route.created_at.desc())
            .limit(limit)
            .all()
        )

        route_list = [
            {
                "id": str(r.id),
                "name": r.name,
                "distance_km": round(r.distance_m / 1000, 1) if r.distance_m else None,
                "route_type": r.route_type,
                "created_at": r.created_at.strftime("%Y-%m-%d"),
            }
            for r in routes
        ]

        count = len(route_list)
        description = f"{count} route{'s' if count != 1 else ''} found" if count else "No routes saved yet"

        return {
            "routes": route_list,
            "count": count,
            "message": description,
            "action_type": "routes_listed",
            "action_title": "Your Routes",
            "action_description": description,
            "action_nav_url": "/routes",
        }

    def _generate_route(
        self, db: Session, user: User, distance_km: float, profile: str = "bike"
    ) -> Dict[str, Any]:
        """Generate a new AI loop route from the user's home location."""
        from app.services.route_generator import route_generation_service

        profile_obj = db.query(Profile).filter(Profile.id == user.id).first()
        start_lat = getattr(profile_obj, "home_lat", None) if profile_obj else None
        start_lng = getattr(profile_obj, "home_lng", None) if profile_obj else None

        if start_lat is None or start_lng is None:
            return {
                "success": False,
                "message": (
                    "No home location set on your profile. "
                    "Please set your location in Profile settings first."
                ),
            }

        result = route_generation_service.generate_ai_loop_route(
            start_lat=start_lat,
            start_lng=start_lng,
            distance_km=distance_km,
            profile=profile,
            route_type="road",
            num_waypoints=4,
            user_id=str(user.id),
            db=db,
        )

        route = result["route"]
        dist = round(route.distance_m / 1000, 1)
        elev = round(route.total_elevation_gain_m or 0, 0)

        return {
            "success": True,
            "route_id": str(route.id),
            "name": route.name,
            "distance_km": dist,
            "elevation_gain_m": elev,
            "message": f"Generated {dist}km loop route: {route.name}",
            "action_type": "route_generated",
            "action_title": f"New Route: {route.name}",
            "action_description": f"{dist}km · {elev}m elevation",
            "action_nav_url": "/routes",
        }

    def _delete_route(
        self, db: Session, user: User, route_name_or_id: str
    ) -> Dict[str, Any]:
        """Delete a route by name or ID."""
        from app.models.route import Route
        from app.core.database import uuid_to_db_format

        user_id_db = uuid_to_db_format(user.id)

        route = (
            db.query(Route)
            .filter(Route.user_id == user_id_db, Route.id == route_name_or_id)
            .first()
        )
        if not route:
            route = (
                db.query(Route)
                .filter(
                    Route.user_id == user_id_db,
                    Route.name.ilike(route_name_or_id),
                )
                .first()
            )

        if not route:
            return {
                "success": False,
                "message": f"No route found named or with ID '{route_name_or_id}'.",
            }

        route_name = route.name
        db.delete(route)
        db.commit()

        return {
            "success": True,
            "deleted_name": route_name,
            "message": f"Deleted route: {route_name}",
            "action_type": "route_deleted",
            "action_title": "Route Deleted",
            "action_description": f"'{route_name}' has been removed",
            "action_nav_url": "/routes",
        }

    def _rename_route(
        self, db: Session, user: User, route_name_or_id: str, new_name: str
    ) -> Dict[str, Any]:
        """Rename a route."""
        from app.models.route import Route
        from app.core.database import uuid_to_db_format
        from datetime import datetime

        user_id_db = uuid_to_db_format(user.id)

        route = (
            db.query(Route)
            .filter(Route.user_id == user_id_db, Route.id == route_name_or_id)
            .first()
        )
        if not route:
            route = (
                db.query(Route)
                .filter(
                    Route.user_id == user_id_db,
                    Route.name.ilike(route_name_or_id),
                )
                .first()
            )

        if not route:
            return {
                "success": False,
                "message": f"No route found named or with ID '{route_name_or_id}'.",
            }

        old_name = route.name
        route.name = new_name
        route.updated_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "old_name": old_name,
            "new_name": new_name,
            "message": f"Renamed '{old_name}' to '{new_name}'",
            "action_type": "route_renamed",
            "action_title": "Route Renamed",
            "action_description": f"'{old_name}' → '{new_name}'",
            "action_nav_url": "/routes",
        }

    # ── Profile Tools ─────────────────────────────────────────────────────────

    def _get_profile(self, db: Session, user: User) -> Dict[str, Any]:
        """Read the user's profile."""
        profile = db.query(Profile).filter(Profile.id == user.id).first()
        if not profile:
            return {"message": "No profile found.", "profile": {}}

        fields = {
            "age": profile.age,
            "gender": profile.gender,
            "weight_lbs": float(profile.weight_lbs) if profile.weight_lbs else None,
            "fitness_level": profile.fitness_level,
            "cycling_experience": profile.cycling_experience,
            "weekly_training_hours": float(profile.weekly_training_hours) if profile.weekly_training_hours else None,
            "primary_goals": profile.primary_goals,
            "equipment_available": profile.equipment_available,
            "preferred_training_days": profile.preferred_training_days,
        }
        fields = {k: v for k, v in fields.items() if v is not None}

        return {
            "profile": fields,
            "message": "Profile retrieved successfully.",
            "action_type": "profile_viewed",
            "action_title": "Your Profile",
            "action_description": f"Fitness: {fields.get('fitness_level', 'not set')} · Goals: {str(fields.get('primary_goals', 'not set'))[:40]}",
            "action_nav_url": "/profile",
        }

    def _update_profile(
        self,
        db: Session,
        user: User,
        weight_lbs: Optional[float] = None,
        fitness_level: Optional[str] = None,
        weekly_training_hours: Optional[float] = None,
        primary_goals: Optional[str] = None,
        equipment_available: Optional[str] = None,
        preferred_training_days: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update user profile fields."""
        from datetime import datetime

        profile = db.query(Profile).filter(Profile.id == user.id).first()
        if not profile:
            return {"success": False, "message": "Profile not found."}

        updated_fields = {}
        if weight_lbs is not None:
            profile.weight_lbs = weight_lbs
            updated_fields["weight_lbs"] = weight_lbs
        if fitness_level is not None:
            profile.fitness_level = fitness_level
            updated_fields["fitness_level"] = fitness_level
        if weekly_training_hours is not None:
            profile.weekly_training_hours = weekly_training_hours
            updated_fields["weekly_training_hours"] = weekly_training_hours
        if primary_goals is not None:
            profile.primary_goals = primary_goals
            updated_fields["primary_goals"] = primary_goals
        if equipment_available is not None:
            profile.equipment_available = equipment_available
            updated_fields["equipment_available"] = equipment_available
        if preferred_training_days is not None:
            profile.preferred_training_days = preferred_training_days
            updated_fields["preferred_training_days"] = preferred_training_days

        if not updated_fields:
            return {"success": False, "message": "No fields provided to update."}

        profile.updated_at = datetime.utcnow()
        db.commit()

        field_names = ", ".join(updated_fields.keys())
        return {
            "success": True,
            "updated_fields": updated_fields,
            "message": f"Profile updated: {field_names}",
            "action_type": "profile_updated",
            "action_title": "Profile Updated",
            "action_description": f"Updated: {field_names}",
            "action_nav_url": "/profile",
        }

    # ── Training Plan Generation & Structured Workout Update ─────────────────

    def _generate_training_plan(
        self, db: Session, user: User, goal: str, weekly_hours: float, fitness_level: str
    ) -> Dict[str, Any]:
        """Generate a new training plan, deactivating any existing active plan."""
        from app.services.training_plan_generator import training_plan_generator
        from app.core.database import uuid_to_db_format

        user_id_db = uuid_to_db_format(user.id)

        existing = (
            db.query(TrainingPlan)
            .filter(TrainingPlan.user_id == user_id_db, TrainingPlan.is_active == True)
            .all()
        )
        for plan in existing:
            plan.is_active = False

        plan_data = training_plan_generator.generate_plan(
            goal=goal,
            weekly_hours=weekly_hours,
            fitness_level=fitness_level,
            preferences=None,
            strava_data=None,
        )

        new_plan = TrainingPlan(
            user_id=user_id_db,
            name=f"{goal} Training Plan",
            goal=goal,
            weekly_hours=weekly_hours,
            start_date=datetime.now(),
            plan_data=plan_data,
            is_active=True,
        )
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)

        return {
            "success": True,
            "plan_id": str(new_plan.id),
            "plan_name": new_plan.name,
            "message": f"Created new training plan: {new_plan.name}",
            "action_type": "training_plan_generated",
            "action_title": f"New Plan: {new_plan.name}",
            "action_description": f"{weekly_hours}h/week · {fitness_level}",
            "action_nav_url": "/training",
        }

    def _update_workout_structured(
        self,
        db: Session,
        user: User,
        day: str,
        title: Optional[str] = None,
        workout_type: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        description: Optional[str] = None,
        week_number: int = 1,
    ) -> Dict[str, Any]:
        """Update a specific day's workout with full field control."""
        try:
            plan = self._get_or_create_user_training_plan(db, user)

            if plan.plan_data is None:
                plan.plan_data = {}
            if "weeks" not in plan.plan_data or not plan.plan_data["weeks"]:
                return {
                    "success": False,
                    "message": "No weeks found in training plan. Generate a plan first.",
                }

            week_idx = min(week_number - 1, len(plan.plan_data["weeks"]) - 1)
            week = plan.plan_data["weeks"][week_idx]

            if "workouts" not in week or day not in week["workouts"]:
                return {"success": False, "message": f"No workout found for {day}."}

            workout = week["workouts"][day]
            old_title = workout.get("title", "Unknown")

            if title is not None:
                workout["title"] = title
            if workout_type is not None:
                workout["workout_type"] = workout_type
            if duration_minutes is not None:
                workout["duration_minutes"] = duration_minutes
            if description is not None:
                workout["description"] = description

            plan.updated_at = datetime.utcnow()
            db.flush()
            db.commit()

            new_title = workout.get("title", old_title)
            day_label = day.capitalize()

            return {
                "success": True,
                "day": day,
                "week": week_number,
                "old_title": old_title,
                "new_title": new_title,
                "message": f"Updated {day_label}: '{old_title}' → '{new_title}'",
                "action_type": "workout_updated",
                "action_title": f"{day_label} Workout Updated",
                "action_description": f"'{old_title}' → '{new_title}'",
                "action_nav_url": "/training",
            }

        except Exception as e:
            db.rollback()
            raise e

    # ── Strava Tools ──────────────────────────────────────────────────────────

    def _get_strava_activities(
        self, db: Session, user: User, limit: int = 5
    ) -> Dict[str, Any]:
        """Fetch recent Strava activities from the API."""
        import requests as http_requests

        limit = min(max(1, limit), 20)
        profile = db.query(Profile).filter(Profile.id == user.id).first()

        if not profile or not profile.strava_access_token:
            return {
                "success": False,
                "message": "Strava is not connected. Connect your account in Settings.",
            }

        response = http_requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers={"Authorization": f"Bearer {profile.strava_access_token}"},
            params={"per_page": limit},
        )

        if response.status_code != 200:
            return {
                "success": False,
                "message": "Could not fetch Strava activities. Your token may have expired — try syncing.",
            }

        acts = response.json()
        activity_list = [
            {
                "name": a.get("name"),
                "date": a.get("start_date_local", "")[:10],
                "distance_km": round(a.get("distance", 0) / 1000, 1),
                "moving_time_min": round(a.get("moving_time", 0) / 60),
                "avg_speed_kmh": round(a.get("average_speed", 0) * 3.6, 1),
                "avg_power_w": a.get("average_watts"),
                "avg_hr_bpm": a.get("average_heartrate"),
                "elevation_m": round(a.get("total_elevation_gain", 0)),
            }
            for a in acts
        ]

        count = len(activity_list)
        description = f"{count} recent activit{'y' if count == 1 else 'ies'} fetched"

        return {
            "success": True,
            "activities": activity_list,
            "count": count,
            "message": description,
            "action_type": "strava_activities_fetched",
            "action_title": "Strava Activities",
            "action_description": description,
            "action_nav_url": "/dashboard",
        }

    def _trigger_strava_sync(self, db: Session, user: User) -> Dict[str, Any]:
        """Trigger a Strava activity sync."""
        import requests as http_requests
        from app.models.strava import StravaActivity

        profile = db.query(Profile).filter(Profile.id == user.id).first()

        if not profile or not profile.strava_access_token:
            return {
                "success": False,
                "message": "Strava is not connected. Connect your account in Settings.",
            }

        response = http_requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers={"Authorization": f"Bearer {profile.strava_access_token}"},
            params={"per_page": 30},
        )

        if response.status_code != 200:
            return {
                "success": False,
                "message": "Failed to connect to Strava. Your token may be expired.",
            }

        activities = response.json()
        synced_count = 0

        for act in activities:
            strava_id = act.get("id")
            if not strava_id:
                continue
            existing = (
                db.query(StravaActivity)
                .filter(StravaActivity.id == strava_id)
                .first()
            )
            if not existing:
                new_act = StravaActivity(
                    id=strava_id,
                    user_id=user.id,
                    name=act.get("name"),
                    summary=act,
                )
                db.add(new_act)
                synced_count += 1

        db.commit()

        description = f"Synced {synced_count} new activit{'y' if synced_count == 1 else 'ies'}"

        return {
            "success": True,
            "synced_count": synced_count,
            "total_checked": len(activities),
            "message": description,
            "action_type": "strava_synced",
            "action_title": "Strava Sync Complete",
            "action_description": description,
            "action_nav_url": "/dashboard",
        }


# Global agent instance
ai_agent = AIAgent()
