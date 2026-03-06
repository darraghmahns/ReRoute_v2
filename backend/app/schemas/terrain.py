from typing import List, Literal, Optional, Tuple

from pydantic import BaseModel, Field, field_validator


class TerrainTarget(BaseModel):
    """
    Terrain constraints for contextual route generation.

    Surface integrity rules (forbidden_osm_surfaces, forbidden_osm_highways) are
    enforced as HARD BLOCKS (multiply_by: 0) in the GraphHopper custom model —
    not as soft priority hints. Road bikes will never be routed onto forbidden surfaces.
    """

    # ── Surface integrity ────────────────────────────────────────────────────
    surface_type: Literal["paved_only", "paved_preferred", "gravel_ok", "any"] = Field(
        "paved_only",
        description=(
            "paved_only: road bike, asphalt/concrete only. "
            "paved_preferred: gravel bike, prefers paved but allows gravel. "
            "gravel_ok: gravel/CX bike, allows unpaved. "
            "any: MTB, no surface restriction."
        ),
    )
    forbidden_osm_highways: List[str] = Field(
        default=["track", "path", "bridleway", "footway"],
        description="OSM highway values to hard-block. Ignored when surface_type='any'.",
    )
    forbidden_osm_surfaces: List[str] = Field(
        default=["dirt", "unpaved", "grass", "sand", "ground"],
        description="OSM surface values to hard-block. Ignored when surface_type='any'. "
        "Values must be valid GH Surface enum entries (mud is encoded as dirt/unpaved in GH).",
    )

    # ── Access control ───────────────────────────────────────────────────────
    allow_private: bool = Field(
        False,
        description="If False, hard-block roads tagged access=private or access=no.",
    )
    allow_no_exit: bool = Field(
        False,
        description="If False, hard-block ways tagged noexit=yes.",
    )

    # ── Elevation targets ────────────────────────────────────────────────────
    ascent_per_km: Optional[float] = Field(
        None,
        ge=0,
        description="Target elevation gain per km (metres). Used for waypoint scoring.",
    )
    total_ascent_m: Optional[float] = Field(
        None,
        ge=0,
        description="Target total elevation gain for the route (metres).",
    )
    max_gradient_pct: Optional[float] = Field(
        None,
        description="Maximum gradient allowed on the route (%). Can be negative for descents.",
    )
    min_gradient_pct: Optional[float] = Field(
        None,
        description="Minimum gradient for the route (%). Use negative for downhill bias.",
    )
    punchiness_score: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description=(
            "0–1. Frequency of short steep efforts. "
            "0 = steady gradient, 1 = repeated punchy climbs like a classic race."
        ),
    )

    # ── Workout structure / flow ─────────────────────────────────────────────
    workout_structure: Optional[
        Literal["interval", "rolling_hills", "tempo", "endurance", "race_simulation"]
    ] = Field(
        None,
        description=(
            "interval: long uninterrupted stretches, avoid junctions. "
            "rolling_hills: repeated short climbs in grade_range. "
            "tempo: sustained moderate gradient. "
            "endurance: any terrain, minimise retracing. "
            "race_simulation: match a race terrain profile."
        ),
    )
    min_uninterrupted_segment_km: Optional[float] = Field(
        None,
        ge=0,
        description=(
            "Minimum km of uninterrupted road required for interval efforts. "
            "Used to penalise short roads and junctions in custom model."
        ),
    )
    grade_range: Optional[Tuple[float, float]] = Field(
        None,
        description=(
            "Target gradient range (min%, max%) for rolling_hills or race_simulation. "
            "Example: (3.0, 6.0) for typical punchy climbs."
        ),
    )

    # ── Race simulation context ───────────────────────────────────────────────
    race_name: Optional[str] = Field(
        None,
        description="Source race name for simulation mode (e.g. 'Paris-Roubaix').",
    )

    # ── Validators ───────────────────────────────────────────────────────────
    @field_validator("grade_range")
    @classmethod
    def grade_range_min_lt_max(
        cls, v: Optional[Tuple[float, float]]
    ) -> Optional[Tuple[float, float]]:
        if v is not None and v[0] >= v[1]:
            raise ValueError(
                f"grade_range min ({v[0]}) must be less than max ({v[1]})"
            )
        return v

    @field_validator("forbidden_osm_highways", "forbidden_osm_surfaces")
    @classmethod
    def no_empty_strings(cls, v: List[str]) -> List[str]:
        for item in v:
            if not item.strip():
                raise ValueError("OSM tag lists must not contain empty strings")
        return v
