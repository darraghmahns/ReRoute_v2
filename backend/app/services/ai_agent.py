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

from app.models.training import TrainingPlan
from app.models.user import User

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
                description="Update specific fields in the user's training plan",
                parameters={
                    "type": "object",
                    "properties": {
                        "field": {
                            "type": "string",
                            "description": "The field to update (e.g., 'weekly_training_hours', 'goal', 'current_phase')",
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

        # Route Generation Tools (placeholders for now)
        self.register_tool(
            AgentTool(
                name="generate_workout_route",
                description="Generate a route optimized for a specific workout type",
                parameters={
                    "type": "object",
                    "properties": {
                        "workout_type": {
                            "type": "string",
                            "enum": [
                                "endurance",
                                "interval",
                                "recovery",
                                "hill_climbing",
                            ],
                            "description": "Type of workout the route should support",
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Target duration for the route in minutes",
                        },
                        "difficulty": {
                            "type": "string",
                            "enum": ["easy", "moderate", "hard"],
                            "description": "Desired difficulty level",
                        },
                        "preferences": {
                            "type": "object",
                            "description": "Additional preferences (avoid traffic, scenic route, etc.)",
                        },
                    },
                    "required": ["workout_type", "duration_minutes"],
                },
                function=self._generate_workout_route,
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

    def _update_training_plan(
        self, db: Session, user: User, field: str, value: str, reason: str
    ) -> Dict[str, Any]:
        """Update a specific field in the user's training plan."""
        try:
            # Get or create training plan
            plan = (
                db.query(TrainingPlan).filter(TrainingPlan.user_id == user.id).first()
            )
            if not plan:
                plan = TrainingPlan(user_id=user.id, details={})
                db.add(plan)

            # Initialize details if needed
            if plan.details is None:
                plan.details = {}

            # Convert value to appropriate type
            processed_value = self._process_value(value)

            # Store the old value for logging
            old_value = plan.details.get(field, "Not set")

            # Update the field
            plan.details[field] = processed_value
            plan.updated_at = datetime.utcnow()

            # Log the change
            if "change_log" not in plan.details:
                plan.details["change_log"] = []

            plan.details["change_log"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "field": field,
                    "old_value": old_value,
                    "new_value": processed_value,
                    "reason": reason,
                    "changed_by": "AI Agent",
                }
            )

            db.commit()

            return {
                "action": "update_training_plan",
                "field": field,
                "old_value": old_value,
                "new_value": processed_value,
                "reason": reason,
                "message": f"Successfully updated {field} from '{old_value}' to '{processed_value}'. Reason: {reason}",
            }

        except Exception as e:
            db.rollback()
            raise e

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
            # Get or create training plan
            plan = (
                db.query(TrainingPlan).filter(TrainingPlan.user_id == user.id).first()
            )
            if not plan:
                plan = TrainingPlan(user_id=user.id, details={})
                db.add(plan)

            if plan.details is None:
                plan.details = {}

            # Initialize training blocks if needed
            if "training_blocks" not in plan.details:
                plan.details["training_blocks"] = []

            # Create new training block
            new_block = {
                "id": len(plan.details["training_blocks"]) + 1,
                "type": block_type,
                "details": details,
                "schedule": schedule,
                "created_at": datetime.utcnow().isoformat(),
                "created_by": "AI Agent",
            }

            plan.details["training_blocks"].append(new_block)
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
        """Analyze training progress and return insights."""
        try:
            # This is a placeholder - in a full implementation, this would:
            # 1. Query Strava activities
            # 2. Analyze trends in the specified metrics
            # 3. Compare against training plan goals
            # 4. Generate recommendations

            return {
                "action": "analyze_training_progress",
                "analysis_type": analysis_type,
                "metrics": metrics or ["power", "distance", "cadence"],
                "insights": [
                    "This is a placeholder analysis",
                    "In the full implementation, this would analyze your Strava data",
                    "And provide specific insights based on your training plan",
                ],
                "recommendations": [
                    "Continue current training pattern",
                    "Consider adding more recovery days",
                    "Focus on consistency over intensity",
                ],
                "message": f"Completed {analysis_type} analysis for specified metrics",
            }

        except Exception as e:
            raise e

    def _generate_workout_route(
        self,
        db: Session,
        user: User,
        workout_type: str,
        duration_minutes: int,
        difficulty: str = "moderate",
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a route for a specific workout type."""
        try:
            # This is a placeholder - in the full implementation, this would:
            # 1. Get user's location/preferred areas
            # 2. Call the route generation service
            # 3. Optimize route for the specific workout type
            # 4. Return the generated route

            return {
                "action": "generate_workout_route",
                "workout_type": workout_type,
                "duration_minutes": duration_minutes,
                "difficulty": difficulty,
                "route": {
                    "id": "placeholder_route_123",
                    "name": f"{workout_type.title()} Route - {duration_minutes} minutes",
                    "distance_km": duration_minutes * 0.4,  # Rough estimate
                    "estimated_time": duration_minutes,
                    "elevation_gain": 100 if workout_type == "hill_climbing" else 50,
                    "description": f"AI-generated route optimized for {workout_type} training",
                },
                "message": f"Generated a {duration_minutes}-minute {workout_type} route for you",
            }

        except Exception as e:
            raise e

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


# Global agent instance
ai_agent = AIAgent()
