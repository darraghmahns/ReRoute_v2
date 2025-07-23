from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_active_user_by_session
from app.models.user import User
from app.models.route import Route, RouteWaypoint, SavedRoute
from app.schemas.route import (
    RouteCreate, RouteUpdate, RouteResponse, RouteListResponse, 
    RouteGenerationResponse, SavedRouteCreate, SavedRoute as SavedRouteSchema,
    GPXExportResponse, RouteGenerationParams
)
from app.services.route_generator import route_generation_service
from typing import List, Optional
import time
import uuid
from datetime import datetime
import logging
from fastapi.responses import Response as FastAPIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routes", tags=["routes"])

@router.post("/generate", response_model=RouteGenerationResponse)
def generate_route(
    params: RouteGenerationParams,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db)
):
    """Generate new route with GraphHopper and Strava integration"""
    try:
        result = route_generation_service.generate_route(params, str(current_user.id), db)
        
        return RouteGenerationResponse(
            message=result["message"],
            route=RouteResponse.from_orm(result["route"]),
            generation_time_ms=result["generation_time_ms"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Route generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Route generation failed: {str(e)}")

@router.get("/", response_model=List[RouteListResponse])
def list_routes(
    skip: int = 0,
    limit: int = 20,
    route_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db)
):
    """List user's routes"""
    query = db.query(Route).filter(Route.user_id == current_user.id)
    
    if route_type:
        query = query.filter(Route.route_type == route_type)
    
    routes = query.offset(skip).limit(limit).all()
    
    return [RouteListResponse.from_orm(route) for route in routes]

@router.get("/{route_id}", response_model=RouteResponse)
def get_route(
    route_id: str,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db)
):
    """Get specific route"""
    route = db.query(Route).filter(
        Route.id == route_id,
        Route.user_id == current_user.id
    ).first()
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return RouteResponse.from_orm(route)

@router.put("/{route_id}", response_model=RouteResponse)
def update_route(
    route_id: str,
    route_update: RouteUpdate,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db)
):
    """Update route"""
    route = db.query(Route).filter(
        Route.id == route_id,
        Route.user_id == current_user.id
    ).first()
    
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
    db: Session = Depends(get_db)
):
    """Delete route"""
    route = db.query(Route).filter(
        Route.id == route_id,
        Route.user_id == current_user.id
    ).first()
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    db.delete(route)
    db.commit()
    
    return {"message": "Route deleted successfully"}

@router.get("/{route_id}/gpx")
def download_gpx(
    route_id: str,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db)
):
    """Download GPX file"""
    route = db.query(Route).filter(
        Route.id == route_id,
        Route.user_id == current_user.id
    ).first()
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Generate GPX content
    gpx_content = _generate_gpx(route)
    
    filename = f"{route.name.replace(' ', '_')}.gpx"
    
    return FastAPIResponse(
        content=gpx_content,
        media_type="application/gpx+xml",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/loops", response_model=RouteGenerationResponse)
def generate_loop(
    lat: float,
    lng: float,
    distance_km: float,
    profile: str = "bike",
    route_type: str = "road",
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db)
):
    """Generate loop route of specified distance"""
    
    params = RouteGenerationParams(
        start_lat=lat,
        start_lng=lng,
        profile=profile,
        route_type=route_type,
        distance_km=distance_km,
        is_loop=True
    )
    
    return generate_route(params, current_user, db)

@router.post("/saved", response_model=SavedRouteSchema)
def save_route(
    save_data: SavedRouteCreate,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db)
):
    """Save a route to user's collection"""
    
    # Check if route exists
    route = db.query(Route).filter(Route.id == save_data.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Check if already saved
    existing = db.query(SavedRoute).filter(
        SavedRoute.user_id == current_user.id,
        SavedRoute.route_id == save_data.route_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Route already saved")
    
    saved_route = SavedRoute(
        user_id=current_user.id,
        route_id=save_data.route_id,
        notes=save_data.notes
    )
    
    db.add(saved_route)
    db.commit()
    db.refresh(saved_route)
    
    return SavedRouteSchema.from_orm(saved_route)

@router.get("/saved", response_model=List[SavedRouteSchema])
def get_saved_routes(
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db)
):
    """Get user's saved routes"""
    
    saved_routes = db.query(SavedRoute).filter(
        SavedRoute.user_id == current_user.id
    ).all()
    
    return [SavedRouteSchema.from_orm(sr) for sr in saved_routes]

@router.get("/{route_id}/suggestions")
def get_route_suggestions(
    route_id: str,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db)
):
    """Get Strava-based route improvement suggestions"""
    
    route = db.query(Route).filter(
        Route.id == route_id,
        Route.user_id == current_user.id
    ).first()
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    from app.services.strava_route_integration import strava_route_integration
    suggestions = strava_route_integration.suggest_route_modifications(
        route.geometry, str(current_user.id), db
    )
    
    return {"suggestions": suggestions}

@router.post("/generate-ai-loop", response_model=RouteGenerationResponse)
def generate_ai_loop_route(
    start_lat: float,
    start_lng: float,
    distance_km: float,
    profile: str = "bike",
    route_type: str = "road",
    num_waypoints: int = 4,
    current_user: User = Depends(get_current_active_user_by_session),
    db: Session = Depends(get_db)
):
    """Generate a loop route using AI waypoint selection and snapping to roads"""
    try:
        result = route_generation_service.generate_ai_loop_route(
            start_lat=start_lat,
            start_lng=start_lng,
            distance_km=distance_km,
            profile=profile,
            route_type=route_type,
            num_waypoints=num_waypoints,
            user_id=str(current_user.id),
            db=db
        )
        
        return RouteGenerationResponse(
            message=result["message"],
            route=RouteResponse.from_orm(result["route"]),
            generation_time_ms=result["generation_time_ms"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"AI loop route generation error: {e}")
        raise HTTPException(status_code=500, detail=f"AI loop route generation failed: {str(e)}")

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
        gpx_content += f"      <trkpt lat=\"{lat}\" lon=\"{lng}\">\n"
        if elevation:
            gpx_content += f"        <ele>{elevation}</ele>\n"
        gpx_content += "      </trkpt>\n"
    
    gpx_content += """    </trkseg>
  </trk>
</gpx>"""
    
    return gpx_content 