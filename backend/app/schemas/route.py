from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class RouteWaypointBase(BaseModel):
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")
    elevation_m: Optional[float] = Field(None, description="Elevation in meters")
    name: Optional[str] = Field(None, description="Waypoint name")
    waypoint_type: str = Field(..., description="Type: start, end, via, poi")

class RouteWaypointCreate(RouteWaypointBase):
    pass

class RouteWaypoint(RouteWaypointBase):
    id: UUID
    route_id: UUID
    sequence: int
    
    class Config:
        from_attributes = True

class RouteGenerationParams(BaseModel):
    start_lat: float = Field(..., description="Starting latitude")
    start_lng: float = Field(..., description="Starting longitude")
    end_lat: Optional[float] = Field(None, description="Ending latitude (optional for loops)")
    end_lng: Optional[float] = Field(None, description="Ending longitude (optional for loops)")
    profile: str = Field(..., description="Routing profile: bike, gravel, mountain")
    route_type: str = Field(..., description="Route type: road, gravel, mountain, urban")
    distance_km: Optional[float] = Field(None, description="Target distance in kilometers")
    is_loop: bool = Field(False, description="Generate a loop route")
    avoid_highways: bool = Field(True, description="Avoid highways")
    elevation_preference: Optional[str] = Field(None, description="flat, rolling, hilly")
    waypoints: Optional[List[RouteWaypointCreate]] = Field([], description="Intermediate waypoints")
    use_strava_segments: bool = Field(False, description="Prefer popular Strava segments")
    strava_activity_type: Optional[str] = Field(None, description="Bike type for Strava data")

class RouteBase(BaseModel):
    name: str = Field(..., description="Route name")
    description: Optional[str] = Field(None, description="Route description")
    route_type: str = Field(..., description="Route type: road, gravel, mountain, urban")
    profile: str = Field(..., description="Routing profile: bike, gravel, mountain")
    is_public: bool = Field(False, description="Make route public")

class RouteCreate(RouteBase):
    generation_params: RouteGenerationParams

class RouteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None

class RouteResponse(RouteBase):
    id: UUID
    user_id: UUID
    geometry: Optional[Dict[str, Any]] = Field(None, description="GeoJSON LineString")
    waypoints: Optional[List[Dict[str, Any]]] = Field(None, description="Route waypoints")
    elevation_profile: Optional[List[Dict[str, Any]]] = Field(None, description="Elevation data")
    distance_m: float
    total_elevation_gain_m: float
    total_elevation_loss_m: float
    estimated_time_s: Optional[int]
    difficulty_score: Optional[float]
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    is_loop: bool
    strava_segments: Optional[List[Dict[str, Any]]] = Field(None, description="Strava segments")
    popularity_score: Optional[float] = Field(None, description="Route popularity score")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RouteListResponse(BaseModel):
    id: UUID
    name: str
    route_type: str
    distance_m: float
    total_elevation_gain_m: float
    difficulty_score: Optional[float]
    is_loop: bool
    is_public: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class RouteGenerationResponse(BaseModel):
    message: str
    route: RouteResponse
    generation_time_ms: int
    
class SavedRouteCreate(BaseModel):
    route_id: UUID
    notes: Optional[str] = None

class SavedRoute(BaseModel):
    id: UUID
    user_id: UUID
    route_id: UUID
    saved_at: datetime
    notes: Optional[str]
    route: RouteResponse
    
    class Config:
        from_attributes = True

class GPXExportResponse(BaseModel):
    filename: str
    content: str
    content_type: str = "application/gpx+xml"