"""
Workout → TerrainTarget mapping for the Workout Integration routing mode.

Each WorkoutType has a deterministic mapping to a TerrainTarget. The mapping
is a plain lookup table — no heuristics or LLM involvement. The intent is
that each mapping is explicit and reviewable by a cycling coach, not inferred.

Speed reference for interval segment length calculations:
  - THRESHOLD: ~24 km/h average (a typical threshold effort on flat/rolling terrain)
  - VO2MAX:    ~22 km/h average (higher effort but shorter, often with headwind effect)
These produce the minimum uninterrupted road length needed for one full interval.
"""
from typing import Dict, Optional

from app.schemas.terrain import TerrainTarget
from app.schemas.training import WorkoutType

# Average speed (km/h) assumed for interval segment length calculations
_THRESHOLD_SPEED_KMH = 24.0
_VO2MAX_SPEED_KMH = 22.0


class WorkoutRoutePlanner:
    """
    Maps a WorkoutType + duration to a TerrainTarget for route generation.

    The caller is responsible for passing the TerrainTarget into
    RouteGenerationParams.terrain_target before calling route_generation_service.
    """

    # ── Workout → TerrainTarget table ─────────────────────────────────────────
    # Each entry is the *base* configuration. Duration-dependent fields
    # (min_uninterrupted_segment_km) are computed in workout_to_terrain_target().
    _BASE_CONFIG: Dict[str, Dict] = {
        WorkoutType.THRESHOLD: {
            "surface_type": "paved_only",
            "grade_range": (0.0, 2.0),
            "workout_structure": "interval",
            "speed_kmh": _THRESHOLD_SPEED_KMH,
        },
        WorkoutType.VO2MAX: {
            "surface_type": "paved_only",
            "grade_range": (0.0, 1.5),
            "workout_structure": "interval",
            "speed_kmh": _VO2MAX_SPEED_KMH,
        },
        WorkoutType.ENDURANCE: {
            "surface_type": "paved_only",
            "grade_range": None,
            "workout_structure": "endurance",
            "speed_kmh": None,
        },
        WorkoutType.RECOVERY: {
            "surface_type": "paved_only",
            "grade_range": (-1.0, 1.0),
            "workout_structure": "endurance",
            "speed_kmh": None,
        },
        WorkoutType.CROSS_TRAINING: {
            "surface_type": "paved_preferred",
            "grade_range": (2.0, 6.0),
            "workout_structure": "rolling_hills",
            "speed_kmh": None,
        },
    }

    def workout_to_terrain_target(
        self,
        workout_type: WorkoutType,
        duration_minutes: int,
        difficulty: str = "moderate",
    ) -> TerrainTarget:
        """
        Return a TerrainTarget for the given workout type and duration.

        Raises ValueError for WorkoutType.REST — rest days have no route.

        difficulty: "easy" | "moderate" | "hard"
          For interval workouts, adjusts the number of expected intervals
          which affects min_uninterrupted_segment_km.
        """
        if workout_type == WorkoutType.REST:
            raise ValueError(
                "WorkoutType.REST does not produce a route — rest days have no training route."
            )

        config = self._BASE_CONFIG.get(workout_type)
        if config is None:
            raise ValueError(
                f"Unknown WorkoutType '{workout_type}'. "
                f"Valid types: {[wt.value for wt in WorkoutType if wt != WorkoutType.REST]}"
            )

        # Compute interval segment length when applicable
        min_uninterrupted_km: Optional[float] = None
        speed_kmh = config.get("speed_kmh")
        if speed_kmh is not None and duration_minutes > 0:
            # One interval effort at the relevant speed:
            # e.g. 10 min @ 24 km/h = 4.0 km minimum uninterrupted stretch
            min_uninterrupted_km = round(
                (duration_minutes * speed_kmh) / 60.0, 2
            )

            # For VO2max, intervals are shorter (reps are typically 3-8 min)
            # halve the segment length requirement to keep the route achievable
            if workout_type == WorkoutType.VO2MAX:
                min_uninterrupted_km = round(min_uninterrupted_km / 2.0, 2)

            # Difficulty modifier: hard → full segment, moderate → 80%, easy → 60%
            difficulty_scale = {"easy": 0.6, "moderate": 0.8, "hard": 1.0}
            scale = difficulty_scale.get(difficulty, 0.8)
            min_uninterrupted_km = round(min_uninterrupted_km * scale, 2)

        return TerrainTarget(
            surface_type=config["surface_type"],
            grade_range=config["grade_range"],
            workout_structure=config["workout_structure"],
            min_uninterrupted_segment_km=min_uninterrupted_km,
            allow_private=False,
            allow_no_exit=False,
        )


# Service instance
workout_route_planner = WorkoutRoutePlanner()
