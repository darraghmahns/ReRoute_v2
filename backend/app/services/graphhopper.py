import requests
import json
from typing import Dict, List, Optional, Tuple, Any
from app.core.config import settings
from app.schemas.route import RouteGenerationParams
import logging
import random
import math

logger = logging.getLogger(__name__)

class GraphHopperService:
    def __init__(self):
        # Use your hosted GraphHopper server
        self.base_url = "https://reroute-graphhopper-server.onrender.com"
        self.timeout = 30
        
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to GraphHopper API"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GraphHopper API error: {e}")
            raise Exception(f"GraphHopper API error: {e}")
    
    def generate_route(self, params: RouteGenerationParams) -> Dict[str, Any]:
        """Generate a route using GraphHopper"""
        
        # Convert profile to GraphHopper profile
        profile_mapping = {
            "bike": "bike",
            "gravel": "gravel", 
            "mountain": "mountain"
        }
        
        gh_profile = profile_mapping.get(params.profile, "bike")
        
        # Build GraphHopper request parameters
        gh_params = {
            "profile": gh_profile,
            "point": [],
            "points_encoded": "false",
            "elevation": "true",
            "instructions": "true", 
            "calc_points": "true"
        }
        
        # Add start point
        gh_params["point"].append(f"{params.start_lat},{params.start_lng}")
        
        # Add waypoints
        if params.waypoints:
            for waypoint in params.waypoints:
                gh_params["point"].append(f"{waypoint.lat},{waypoint.lng}")
        
        # Add end point 
        if not params.is_loop and params.end_lat and params.end_lng:
            # Point-to-point route
            gh_params["point"].append(f"{params.end_lat},{params.end_lng}")
        elif params.is_loop:
            # Loop route - add start point again as end point after waypoints
            gh_params["point"].append(f"{params.start_lat},{params.start_lng}")
        
        # Add custom model parameters for route preferences
        custom_model = self._build_custom_model(params)
        if custom_model:
            gh_params["custom_model"] = json.dumps(custom_model)
        
        # Debug logging
        logger.info(f"GraphHopper request params: profile={gh_params.get('profile')}, points={gh_params.get('point')}")
        if custom_model:
            logger.info(f"Custom model priority rules: {len(custom_model.get('priority', []))} rules for route_type={params.route_type}")
        
        # Make request to GraphHopper
        return self._make_request("route", gh_params)
    
    def _build_custom_model(self, params: RouteGenerationParams) -> Optional[Dict[str, Any]]:
        """Build custom model based on route preferences"""
        # For road bikes, use extremely strict custom model to force paved roads only
        if params.route_type == "road" or params.profile == "bike":
            logger.info("Using ultra-strict custom model to force paved roads only for road bikes")
            return {
                "speed": [
                    # Block ALL unpaved surfaces and trails completely
                    {"if": "road_class == TRACK", "multiply_by": "0"},
                    {"if": "road_class == PATH", "multiply_by": "0"},
                    {"if": "road_class == FOOTWAY", "multiply_by": "0"},
                    {"if": "road_class == BRIDLEWAY", "multiply_by": "0"},
                    {"if": "road_class == STEPS", "multiply_by": "0"},
                    {"if": "surface == UNPAVED", "multiply_by": "0"},
                    {"if": "surface == GRAVEL", "multiply_by": "0"},
                    {"if": "surface == DIRT", "multiply_by": "0"},
                    {"if": "surface == SAND", "multiply_by": "0"},
                    {"if": "surface == GRASS", "multiply_by": "0"},
                    {"if": "surface == GROUND", "multiply_by": "0"},
                    {"if": "surface == COMPACTED", "multiply_by": "0"},
                    {"if": "surface == COBBLESTONE", "multiply_by": "0"},
                    {"if": "surface == WOOD", "multiply_by": "0"},
                    # CRITICAL: Block any road without explicit paved surface
                    {"if": "surface != ASPHALT && surface != CONCRETE && surface != PAVED", "multiply_by": "0"},
                    # Only allow explicitly paved roads
                    {"if": "surface == ASPHALT", "multiply_by": "1.0"},
                    {"if": "surface == CONCRETE", "multiply_by": "1.0"},
                    {"if": "surface == PAVED", "multiply_by": "1.0"}
                ],
                "priority": [
                    # Identical blocking rules for priority
                    {"if": "road_class == TRACK", "multiply_by": "0"},
                    {"if": "road_class == PATH", "multiply_by": "0"},
                    {"if": "road_class == FOOTWAY", "multiply_by": "0"},
                    {"if": "road_class == BRIDLEWAY", "multiply_by": "0"},
                    {"if": "road_class == STEPS", "multiply_by": "0"},
                    {"if": "surface == UNPAVED", "multiply_by": "0"},
                    {"if": "surface == GRAVEL", "multiply_by": "0"},
                    {"if": "surface == DIRT", "multiply_by": "0"},
                    {"if": "surface == SAND", "multiply_by": "0"},
                    {"if": "surface == GRASS", "multiply_by": "0"},
                    {"if": "surface == GROUND", "multiply_by": "0"},
                    {"if": "surface == COMPACTED", "multiply_by": "0"},
                    {"if": "surface == COBBLESTONE", "multiply_by": "0"},
                    {"if": "surface == WOOD", "multiply_by": "0"},
                    # CRITICAL: Block any road without explicit paved surface
                    {"if": "surface != ASPHALT && surface != CONCRETE && surface != PAVED", "multiply_by": "0"},
                    # Strongly prefer major paved roads
                    {"if": "road_class == PRIMARY && (surface == ASPHALT || surface == CONCRETE || surface == PAVED)", "multiply_by": "2.0"},
                    {"if": "road_class == SECONDARY && (surface == ASPHALT || surface == CONCRETE || surface == PAVED)", "multiply_by": "1.8"},
                    {"if": "road_class == TERTIARY && (surface == ASPHALT || surface == CONCRETE || surface == PAVED)", "multiply_by": "1.5"},
                    {"if": "road_class == RESIDENTIAL && (surface == ASPHALT || surface == CONCRETE || surface == PAVED)", "multiply_by": "1.3"},
                    {"if": "road_class == CYCLEWAY", "multiply_by": "2.0"},
                    {"if": "surface == ASPHALT", "multiply_by": "1.5"},
                    {"if": "surface == CONCRETE", "multiply_by": "1.4"},
                    {"if": "surface == PAVED", "multiply_by": "1.5"}
                ],
                "areas": {"type": "FeatureCollection", "features": []}
            }
        
        # Only use custom models for gravel and mountain bikes
        custom_model = {
            "speed": [],
            "priority": [],
            "areas": {
                "type": "FeatureCollection",
                "features": []
            }
        }
        
        if params.route_type == "gravel":
            # Gravel bike: Allow unpaved surfaces that road bikes avoid
            custom_model["priority"].extend([
                {"if": "surface == GRAVEL", "multiply_by": "1.5"},
                {"if": "surface == UNPAVED", "multiply_by": "1.3"},
                {"if": "road_class == UNCLASSIFIED", "multiply_by": "1.2"},
                {"if": "road_class == TRACK && surface == GRAVEL", "multiply_by": "1.1"}
            ])
            
        elif params.route_type == "mountain":
            # Mountain bike: Allow trails and rough surfaces
            custom_model["priority"].extend([
                {"if": "road_class == TRACK", "multiply_by": "1.5"},
                {"if": "road_class == PATH", "multiply_by": "1.3"},
                {"if": "surface == DIRT", "multiply_by": "1.2"},
                {"if": "surface == GRAVEL", "multiply_by": "1.1"}
            ])
        
        return custom_model if custom_model["priority"] else None
    
    def generate_loop_route(self, lat: float, lng: float, distance_km: float, 
                           profile: str = "bike", route_type: str = "road") -> Dict[str, Any]:
        """Generate a loop route of specified distance"""
        
        # Create loop generation parameters
        params = RouteGenerationParams(
            start_lat=lat,
            start_lng=lng,
            end_lat=lat,
            end_lng=lng,
            profile=profile,
            route_type=route_type,
            distance_km=distance_km,
            is_loop=True
        )
        
        return self.generate_route(params)
    
    def get_isochrone(self, lat: float, lng: float, time_limit: int = 1800, 
                     profile: str = "bike") -> Dict[str, Any]:
        """Get isochrone (reachable area) from a point"""
        
        gh_params = {
            "point": f"{lat},{lng}",
            "time_limit": time_limit,
            "profile": profile,
            "buckets": "3"
        }
        
        return self._make_request("isochrone", gh_params)
    
    def matrix_request(self, points: List[Tuple[float, float]], 
                      profile: str = "bike") -> Dict[str, Any]:
        """Calculate distance/time matrix between multiple points"""
        
        gh_params = {
            "profile": profile,
            "point": [f"{lat},{lng}" for lat, lng in points],
            "out_arrays": ["times", "distances"]
        }
        
        return self._make_request("matrix", gh_params)
    
    def health_check(self) -> bool:
        """Check if GraphHopper service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/healthcheck", timeout=5)
            return response.status_code == 200
        except:
            return False

    def _snap_to_road(self, lat: float, lng: float, profile: str = "bike") -> Tuple[float, float]:
        """Snap a point to the nearest road using GraphHopper's /nearest endpoint"""
        try:
            url = f"{self.base_url}/nearest"
            params = {"point": f"{lat},{lng}", "profile": profile}
            response = requests.get(url, params=params, timeout=self.timeout)
            
            # If /nearest endpoint doesn't exist (404) or has server errors (500), return original coordinates
            if response.status_code in [404, 500]:
                logger.warning(f"/nearest endpoint unavailable (status {response.status_code}), using original coordinates: {lat}, {lng}")
                return lat, lng
                
            response.raise_for_status()
            data = response.json()
            mapped = data.get("mapped_point")
            if mapped:
                snapped_lat, snapped_lng = mapped["lat"], mapped["lon"]
                logger.debug(f"Snapped {lat:.6f},{lng:.6f} to {snapped_lat:.6f},{snapped_lng:.6f}")
                return snapped_lat, snapped_lng
            # fallback to input if not found
            return lat, lng
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [404, 500]:
                logger.warning(f"/nearest endpoint error (status {e.response.status_code}), using original coordinates: {lat}, {lng}")
                return lat, lng
            else:
                logger.error(f"HTTP error snapping to road: {e}")
                return lat, lng
        except Exception as e:
            logger.error(f"Error snapping to road: {e}")
            return lat, lng

    def _generate_loop_waypoints(self, start_lat: float, start_lng: float, num_points: int, radius_m: float, profile: str = "bike") -> List[Dict[str, float]]:
        """Generate waypoints in a circle and snap them to roads"""
        R = 6378137  # Earth radius in meters
        waypoints = []
        
        # Use the provided radius but add some bounds checking
        adjusted_radius = radius_m
        
        for i in range(num_points):
            # Add moderate randomness to create interesting shapes
            base_angle = 2 * math.pi * i / num_points
            angle_offset = random.uniform(-0.2, 0.2)  # Moderate random offset
            angle = base_angle + angle_offset
            
            # Add controlled radius variation 
            radius_variation = random.uniform(0.8, 1.2)  # 20% radius variation (less extreme)
            current_radius = adjusted_radius * radius_variation
            
            dx = current_radius * math.cos(angle)
            dy = current_radius * math.sin(angle)
            dlat = dy / R
            dlng = dx / (R * math.cos(math.pi * start_lat / 180))
            lat = start_lat + (dlat * 180 / math.pi)
            lng = start_lng + (dlng * 180 / math.pi)
            snapped_lat, snapped_lng = self._snap_to_road(lat, lng, profile)
            waypoints.append({"lat": snapped_lat, "lng": snapped_lng})
        return waypoints

    def _generate_conservative_waypoints(self, start_lat: float, start_lng: float, num_points: int, radius_m: float, profile: str = "bike") -> List[Dict[str, float]]:
        """Generate waypoints with much more conservative placement to avoid huge routes"""
        R = 6378137  # Earth radius in meters
        waypoints = []
        
        for i in range(num_points):
            # Create more regular spacing with minimal randomness
            base_angle = 2 * math.pi * i / num_points
            angle_offset = random.uniform(-0.05, 0.05)  # Very small random offset
            angle = base_angle + angle_offset
            
            # Very minimal radius variation to keep routes predictable
            radius_variation = random.uniform(0.9, 1.1)  # Only 10% variation
            current_radius = radius_m * radius_variation
            
            dx = current_radius * math.cos(angle)
            dy = current_radius * math.sin(angle)
            dlat = dy / R
            dlng = dx / (R * math.cos(math.pi * start_lat / 180))
            lat = start_lat + (dlat * 180 / math.pi)
            lng = start_lng + (dlng * 180 / math.pi)
            snapped_lat, snapped_lng = self._snap_to_road(lat, lng, profile)
            waypoints.append({"lat": snapped_lat, "lng": snapped_lng})
        return waypoints

    def generate_ai_loop_route(self, start_lat: float, start_lng: float, distance_km: float, profile: str = "bike", route_type: str = "road", num_waypoints: int = 4) -> Dict[str, Any]:
        """Generate a loop route with iterative distance targeting"""
        try:
            target_distance_m = distance_km * 1000
            tolerance = 0.15  # 15% tolerance
            max_attempts = 5
            
            best_route = None
            best_distance_diff = float('inf')
            
            logger.info(f"Targeting {distance_km:.1f}km loop from {start_lat:.4f},{start_lng:.4f}")
            
            # For GraphHopper to create a proper loop, we need to:
            # 1. Start at the origin point
            # 2. Go through one or more waypoints 
            # 3. Return to the origin point
            # The key is NOT setting end_lat/end_lng in RouteGenerationParams for loops
            
            from app.schemas.route import RouteGenerationParams, RouteWaypointCreate
            
            # Try different waypoint configurations to hit target distance
            for attempt in range(max_attempts):
                try:
                    # Calculate waypoint distance based on target distance and attempt
                    base_waypoint_distance_km = distance_km / 4  # Start with 1/4 of target distance
                    waypoint_distance_km = base_waypoint_distance_km * (1 + attempt * 0.5)  # Increase with each attempt
                    
                    # Limit waypoint distance to reasonable bounds
                    waypoint_distance_km = min(max(waypoint_distance_km, 1.0), 25.0)
                    
                    # Create a strategic waypoint that should create a loop of roughly the target distance
                    waypoint_bearing = 90 + (attempt * 45)  # Vary bearing with each attempt
                    waypoint_lat, waypoint_lng = self._get_waypoint_at_distance(
                        start_lat, start_lng, waypoint_distance_km, waypoint_bearing
                    )
                    
                    # Try to snap waypoint to road network, but continue if it fails
                    try:
                        waypoint_lat, waypoint_lng = self._snap_to_road(waypoint_lat, waypoint_lng, profile)
                    except Exception as e:
                        logger.warning(f"Road snapping failed for waypoint, using original coordinates: {e}")
                        # Continue with original coordinates
                    
                    logger.info(f"Attempt {attempt + 1}: Waypoint at {waypoint_distance_km:.1f}km, bearing {waypoint_bearing}°")
                    
                    # Create route parameters - crucially, do NOT set end_lat/end_lng for loops
                    loop_params = RouteGenerationParams(
                        start_lat=start_lat,
                        start_lng=start_lng,
                        # For loops, we omit end_lat and end_lng - GraphHopper will return to start automatically
                        profile=profile,
                        route_type=route_type,
                        distance_km=distance_km,
                        is_loop=True,
                        waypoints=[RouteWaypointCreate(lat=waypoint_lat, lng=waypoint_lng, waypoint_type="via")]
                    )
                    
                    # Generate the route
                    response = self.generate_route(loop_params)
                    
                    if "paths" in response and response["paths"]:
                        actual_distance_m = response["paths"][0]["distance"]
                        actual_distance_km = actual_distance_m / 1000
                        distance_diff = abs(actual_distance_m - target_distance_m)
                        distance_ratio = distance_diff / target_distance_m
                        
                        logger.info(f"Attempt {attempt + 1}: Generated {actual_distance_km:.1f}km route, target {distance_km:.1f}km, diff={distance_ratio:.1%}")
                        
                        # Check if within tolerance
                        if distance_ratio <= tolerance:
                            logger.info(f"Found good route on attempt {attempt + 1}!")
                            return response
                        
                        # Track best attempt so far
                        if distance_diff < best_distance_diff:
                            best_distance_diff = distance_diff
                            best_route = response
                            logger.info(f"New best route: {actual_distance_km:.1f}km")
                    
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    continue
            
            # Return best attempt if we couldn't find one within tolerance
            if best_route:
                actual_km = best_route["paths"][0]["distance"] / 1000
                logger.info(f"Returning best route: Target={distance_km:.1f}km, Actual={actual_km:.1f}km")
                return best_route
            else:
                raise Exception("All route generation attempts failed")
                
        except Exception as e:
            logger.error(f"AI loop route generation failed: {e}")
            raise

    def _get_waypoint_at_distance(self, start_lat: float, start_lng: float, distance_km: float, bearing_degrees: float) -> tuple[float, float]:
        """Calculate lat/lng of a point at given distance and bearing from start point"""
        R = 6378137  # Earth radius in meters
        distance_m = distance_km * 1000
        
        bearing_rad = math.radians(bearing_degrees)
        lat1_rad = math.radians(start_lat)
        lng1_rad = math.radians(start_lng)
        
        lat2_rad = math.asin(
            math.sin(lat1_rad) * math.cos(distance_m / R) +
            math.cos(lat1_rad) * math.sin(distance_m / R) * math.cos(bearing_rad)
        )
        
        lng2_rad = lng1_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(distance_m / R) * math.cos(lat1_rad),
            math.cos(distance_m / R) - math.sin(lat1_rad) * math.sin(lat2_rad)
        )
        
        return math.degrees(lat2_rad), math.degrees(lng2_rad)

# Service instance
graphhopper_service = GraphHopperService()