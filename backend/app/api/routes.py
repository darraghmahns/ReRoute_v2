import logging
import time
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.orm import Session

from app.core.database import get_db, uuid_to_db_format
from app.core.security import get_current_active_user_by_session
from app.models.route import Route, RouteWaypoint, SavedRoute
from app.models.user import User
from app.schemas.route import (
    GPXExportResponse,
    RouteCreate,
    RouteGenerationParams,
    RouteGenerationResponse,
    RouteListResponse,
    RouteResponse,
    RouteUpdate,
)
from app.schemas.training import WorkoutType
from app.services.usage_service import check_and_log_usage
from app.services.workout_route_planner import workout_route_planner
from app.services.terrain_research_agent import terrain_research_agent
from app.schemas.route import SavedRoute as SavedRouteSchema
from app.schemas.route import SavedRouteCreate
from app.services.route_generator import route_generation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("/generate", response_model=RouteGenerationResponse)
def generate_route(
    params: RouteGenerationParams,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Generate new route with GraphHopper and Strava integration"""
    try:
        result = route_generation_service.generate_route(
            params, str(current_user.id), db
        )

        return RouteGenerationResponse(
            message=result["message"],
            route=RouteResponse.from_orm(result["route"]),
            generation_time_ms=result["generation_time_ms"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Route generation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Route generation failed: {str(e)}"
        )


@router.get("/", response_model=List[RouteListResponse])
def list_routes(
    skip: int = 0,
    limit: int = 20,
    route_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """List user's routes"""
    query = db.query(Route).filter(Route.user_id == uuid_to_db_format(current_user.id))

    if route_type:
        query = query.filter(Route.route_type == route_type)

    routes = query.offset(skip).limit(limit).all()

    return [RouteListResponse.from_orm(route) for route in routes]


@router.get("/{route_id}", response_model=RouteResponse)
def get_route(
    route_id: str,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Get specific route"""
    route = (
        db.query(Route)
        .filter(Route.id == route_id, Route.user_id == uuid_to_db_format(current_user.id))
        .first()
    )

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    return RouteResponse.from_orm(route)


@router.put("/{route_id}", response_model=RouteResponse)
def update_route(
    route_id: str,
    route_update: RouteUpdate,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Update route"""
    route = (
        db.query(Route)
        .filter(Route.id == route_id, Route.user_id == uuid_to_db_format(current_user.id))
        .first()
    )

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    update_data = route_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(route, field, value)

    route.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(route)

    return RouteResponse.from_orm(route)


@router.delete("/{route_id}")
def delete_route(
    route_id: str,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Delete route"""
    route = (
        db.query(Route)
        .filter(Route.id == route_id, Route.user_id == uuid_to_db_format(current_user.id))
        .first()
    )

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    db.delete(route)
    db.commit()

    return {"message": "Route deleted successfully"}


@router.get("/{route_id}/gpx")
def download_gpx(
    route_id: str,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Download GPX file"""
    route = (
        db.query(Route)
        .filter(Route.id == route_id, Route.user_id == uuid_to_db_format(current_user.id))
        .first()
    )

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # Generate GPX content
    gpx_content = _generate_gpx(route)

    filename = f"{route.name.replace(' ', '_')}.gpx"

    return FastAPIResponse(
        content=gpx_content,
        media_type="application/gpx+xml",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/loops", response_model=RouteGenerationResponse)
def generate_loop(
    lat: float,
    lng: float,
    distance_km: float,
    profile: str = "bike",
    route_type: str = "road",
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Generate loop route of specified distance"""

    params = RouteGenerationParams(
        start_lat=lat,
        start_lng=lng,
        profile=profile,
        route_type=route_type,
        distance_km=distance_km,
        is_loop=True,
    )

    return generate_route(params, current_user, db)


@router.post("/saved", response_model=SavedRouteSchema)
def save_route(
    save_data: SavedRouteCreate,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Save a route to user's collection"""

    # Check if route exists
    route = db.query(Route).filter(Route.id == save_data.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # Check if already saved
    existing = (
        db.query(SavedRoute)
        .filter(
            SavedRoute.user_id == uuid_to_db_format(current_user.id),
            SavedRoute.route_id == save_data.route_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="Route already saved")

    saved_route = SavedRoute(
        user_id=uuid_to_db_format(current_user.id), route_id=save_data.route_id, notes=save_data.notes
    )

    db.add(saved_route)
    db.commit()
    db.refresh(saved_route)

    return SavedRouteSchema.from_orm(saved_route)


@router.get("/saved", response_model=List[SavedRouteSchema])
def get_saved_routes(
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Get user's saved routes"""

    saved_routes = (
        db.query(SavedRoute).filter(SavedRoute.user_id == uuid_to_db_format(current_user.id)).all()
    )

    return [SavedRouteSchema.from_orm(sr) for sr in saved_routes]


@router.get("/{route_id}/suggestions")
def get_route_suggestions(
    route_id: str,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Get Strava-based route improvement suggestions"""

    route = (
        db.query(Route)
        .filter(Route.id == route_id, Route.user_id == uuid_to_db_format(current_user.id))
        .first()
    )

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    from app.services.strava_route_integration import strava_route_integration

    suggestions = strava_route_integration.suggest_route_modifications(
        route.geometry, str(current_user.id), db
    )

    return {"suggestions": suggestions}


@router.post("/generate-workout", response_model=RouteGenerationResponse)
def generate_workout_route(
    workout_type: WorkoutType,
    duration_minutes: int,
    start_lat: float,
    start_lng: float,
    profile: str = "bike",
    difficulty: str = "moderate",
    target_distance_km: Optional[float] = None,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """
    Generate a route optimised for a specific workout type and duration.

    The workout type and duration are mapped to a TerrainTarget (surface type,
    grade range, minimum uninterrupted segment length) which constrains the
    GraphHopper routing engine. Surface integrity is enforced as a hard block —
    a road bike will never be routed onto unpaved surfaces.

    difficulty: "easy" | "moderate" | "hard" — scales interval segment requirements.
    """
    try:
        terrain_target = workout_route_planner.workout_to_terrain_target(
            workout_type=workout_type,
            duration_minutes=duration_minutes,
            difficulty=difficulty,
        )

        # Estimate target distance when not explicitly provided
        if target_distance_km is None:
            avg_speed_kmh = 24.0
            target_distance_km = round(
                min(max((duration_minutes / 60.0) * avg_speed_kmh, 5.0), 200.0), 1
            )

        # Delegate to generate_ai_loop_route which handles multi-bearing retry logic
        # (bearing=90 can hit the sea in coastal cities; the AI loop tries 5 bearings).
        result = route_generation_service.generate_ai_loop_route(
            start_lat=start_lat,
            start_lng=start_lng,
            distance_km=target_distance_km,
            profile=profile,
            route_type="road",
            num_waypoints=1,
            user_id=str(current_user.id),
            db=db,
            terrain_target=terrain_target,
        )

        return RouteGenerationResponse(
            message=result["message"],
            route=RouteResponse.from_orm(result["route"]),
            generation_time_ms=result["generation_time_ms"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Workout route generation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Workout route generation failed: {str(e)}"
        )


@router.post("/simulate-race", response_model=RouteGenerationResponse)
def simulate_race_route(
    race_name: str,
    start_lat: float,
    start_lng: float,
    profile: str = "bike",
    target_distance_km: Optional[float] = None,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """
    Generate a local training route that mimics a target race's terrain profile.

    The agent researches the named race (elevation, gradient, surface type, punchiness)
    via LLM, with a fallback to Strava segment data if LLM confidence is insufficient.
    The resulting TerrainTarget is used to constrain GraphHopper routing.

    target_distance_km: scale the simulation to a shorter/longer local route
      while preserving the ascent-per-km ratio. Defaults to 40km.
    """
    try:
        terrain_target = terrain_research_agent.research_race(
            race_name=race_name,
            user_lat=start_lat,
            user_lng=start_lng,
            db=db,
            user_id=str(current_user.id),
            target_distance_km=target_distance_km,
        )

        route_distance_km = target_distance_km or 40.0

        result = route_generation_service.generate_ai_loop_route(
            start_lat=start_lat,
            start_lng=start_lng,
            distance_km=route_distance_km,
            profile=profile,
            route_type="road",
            num_waypoints=1,
            user_id=str(current_user.id),
            db=db,
            terrain_target=terrain_target,
        )

        return RouteGenerationResponse(
            message=result["message"],
            route=RouteResponse.from_orm(result["route"]),
            generation_time_ms=result["generation_time_ms"],
        )

    except Exception as e:
        logger.error(f"Race simulation route error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Race simulation failed: {str(e)}"
        )


@router.post("/generate-ai-loop", response_model=RouteGenerationResponse)
def generate_ai_loop_route(
    start_lat: float,
    start_lng: float,
    distance_km: float,
    profile: str = "bike",
    route_type: str = "road",
    num_waypoints: int = 4,
    via_lat: Optional[float] = None,
    via_lng: Optional[float] = None,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db),
):
    """Generate a loop route using AI waypoint selection and snapping to roads.

    Optionally pass via_lat/via_lng to force the route through a user-specified
    point (e.g. a trailhead) instead of automated waypoint selection.
    """
    # Check free tier limit: 3 routes per month
    allowed, msg = check_and_log_usage(db, current_user, "route_generation", limit_free=3)
    if not allowed:
        raise HTTPException(status_code=403, detail=msg)

    try:
        result = route_generation_service.generate_ai_loop_route(
            start_lat=start_lat,
            start_lng=start_lng,
            distance_km=distance_km,
            profile=profile,
            route_type=route_type,
            num_waypoints=num_waypoints,
            user_id=str(current_user.id),
            db=db,
            via_lat=via_lat,
            via_lng=via_lng,
        )

        return RouteGenerationResponse(
            message=result["message"],
            route=RouteResponse.from_orm(result["route"]),
            generation_time_ms=result["generation_time_ms"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"AI loop route generation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"AI loop route generation failed: {str(e)}"
        )


def _generate_gpx(route: Route) -> str:
    """Generate GPX content for a route"""

    coords = route.geometry["coordinates"]

    gpx_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Reroute" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata>
    <name>{route.name}</name>
    <desc>{route.description or 'Generated by Reroute'}</desc>
    <time>{route.created_at.isoformat()}Z</time>
  </metadata>
  <trk>
    <name>{route.name}</name>
    <type>{route.route_type}</type>
    <trkseg>
"""

    for coord in coords:
        lng, lat = coord[:2]
        elevation = coord[2] if len(coord) > 2 else 0
        gpx_content += f'      <trkpt lat="{lat}" lon="{lng}">\n'
        if elevation:
            gpx_content += f"        <ele>{elevation}</ele>\n"
        gpx_content += "      </trkpt>\n"

    gpx_content += """    </trkseg>
  </trk>
</gpx>"""

    return gpx_content
