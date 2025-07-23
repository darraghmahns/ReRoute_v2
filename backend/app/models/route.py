from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean, JSON, DECIMAL
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import uuid

class Route(Base):
    __tablename__ = "routes"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Route type and profile
    route_type = Column(String(50), nullable=False)  # road, gravel, mountain, urban
    profile = Column(String(50), nullable=False)  # bike, gravel, mountain
    
    # Route geometry and data
    geometry = Column(JSON)  # GeoJSON LineString
    waypoints = Column(JSON)  # Array of lat/lng waypoints
    elevation_profile = Column(JSON)  # Array of elevation points
    
    # Route metrics
    distance_m = Column(Float, nullable=False)
    total_elevation_gain_m = Column(Float, default=0)
    total_elevation_loss_m = Column(Float, default=0)
    estimated_time_s = Column(Integer)
    difficulty_score = Column(Float)  # 1-10 scale
    
    # Start/end coordinates
    start_lat = Column(Float, nullable=False)
    start_lng = Column(Float, nullable=False)
    end_lat = Column(Float, nullable=False)
    end_lng = Column(Float, nullable=False)
    
    # Generation parameters
    generation_params = Column(JSON)  # Store generation parameters used
    graphhopper_response = Column(JSON)  # Store full GraphHopper response
    
    # Strava integration
    strava_segments = Column(JSON)  # Array of Strava segments on this route
    popularity_score = Column(Float)  # Based on Strava heatmap data
    
    # Metadata
    is_loop = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="routes")

class RouteWaypoint(Base):
    __tablename__ = "route_waypoints"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(PostgresUUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    sequence = Column(Integer, nullable=False)  # Order of waypoint in route
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    elevation_m = Column(Float)
    name = Column(String(200))  # Optional waypoint name
    waypoint_type = Column(String(50))  # start, end, via, poi
    
    # Relationships
    route = relationship("Route")

class SavedRoute(Base):
    __tablename__ = "saved_routes"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    route_id = Column(PostgresUUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    saved_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    
    # Relationships
    user = relationship("User")
    route = relationship("Route")