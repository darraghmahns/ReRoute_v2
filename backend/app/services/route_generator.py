import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.route import Route
from app.schemas.route import RouteGenerationParams
from app.services.graphhopper import graphhopper_service
from app.services.strava_route_integration import strava_route_integration

logger = logging.getLogger(__name__)


class RouteGenerationService:
    """Centralized service for route generation and processing"""

    def __init__(self):
        self.graphhopper = graphhopper_service
        self.strava_integration = strava_route_integration

    def generate_route(
        self, params: RouteGenerationParams, user_id: str, db: Session
    ) -> Dict[str, Any]:
        """Generate a route and save to database"""
        start_time = time.time()

        try:
            # Generate route using GraphHopper
            gh_response = self.graphhopper.generate_route(params)

            if "paths" not in gh_response or not gh_response["paths"]:
                raise ValueError("No route found")

            # Process route data
            route_data = self._process_route_response(gh_response, params)

            # Create database record
            route = self._create_route_record(route_data, params, user_id, gh_response)

            # Add Strava integration if requested
            if params.use_strava_segments:
                self._enhance_with_strava(route, user_id, db)

            # Calculate difficulty score
            route.difficulty_score = self._calculate_difficulty(route, params)

            # Save to database
            db.add(route)
            db.commit()
            db.refresh(route)

            generation_time = int((time.time() - start_time) * 1000)

            return {
                "route": route,
                "generation_time_ms": generation_time,
                "message": "Route generated successfully",
            }

        except Exception as e:
            logger.error(f"Route generation error: {e}")
            raise

    def generate_ai_loop_route(
        self,
        start_lat: float,
        start_lng: float,
        distance_km: float,
        profile: str,
        route_type: str,
        num_waypoints: int,
        user_id: str,
        db: Session,
    ) -> Dict[str, Any]:
        """Generate AI-powered loop route"""
        try:
            # Generate using GraphHopper AI loop
            gh_response = self.graphhopper.generate_ai_loop_route(
                start_lat=start_lat,
                start_lng=start_lng,
                distance_km=distance_km,
                profile=profile,
                route_type=route_type,
                num_waypoints=num_waypoints,
            )

            if "paths" not in gh_response or not gh_response["paths"]:
                raise ValueError("No route found")

            # Create params object for processing
            params = RouteGenerationParams(
                start_lat=start_lat,
                start_lng=start_lng,
                end_lat=start_lat,
                end_lng=start_lng,
                profile=profile,
                route_type=route_type,
                distance_km=distance_km,
                is_loop=True,
            )

            # Process using standard route processing
            route_data = self._process_route_response(gh_response, params)
            route = self._create_route_record(route_data, params, user_id, gh_response)
            route.name = f"AI Loop Route - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            # Save to database
            db.add(route)
            db.commit()
            db.refresh(route)

            return {
                "route": route,
                "generation_time_ms": 0,  # Could be timed if needed
                "message": "AI loop route generated successfully",
            }

        except Exception as e:
            logger.error(f"AI loop route generation error: {e}")
            raise

    def _process_route_response(
        self, gh_response: Dict[str, Any], params: RouteGenerationParams
    ) -> Dict[str, Any]:
        """Extract and process route data from GraphHopper response"""
        path = gh_response["paths"][0]

        # Debug logging to see what GraphHopper returns
        logger.info(f"GraphHopper path keys: {list(path.keys())}")
        if "points" in path:
            logger.info(
                f"Points structure: {list(path['points'].keys()) if isinstance(path['points'], dict) else 'not dict'}"
            )
            if (
                "coordinates" in path["points"]
                and len(path["points"]["coordinates"]) > 0
            ):
                coord_sample = path["points"]["coordinates"][0]
                logger.info(
                    f"Sample coordinate: {coord_sample} (length: {len(coord_sample)})"
                )

        # Extract basic route data
        geometry = {"type": "LineString", "coordinates": path["points"]["coordinates"]}

        distance_m = path["distance"]
        time_ms = path["time"]

        # Calculate elevation data
        elevation_gain, elevation_loss = self._calculate_elevation(path)

        # Get start/end coordinates
        coords = geometry["coordinates"]
        start_coord = coords[0]
        end_coord = coords[-1]

        return {
            "geometry": geometry,
            "distance_m": distance_m,
            "time_ms": time_ms,
            "elevation_gain": elevation_gain,
            "elevation_loss": elevation_loss,
            "start_coord": start_coord,
            "end_coord": end_coord,
        }

    def _calculate_elevation(self, path: Dict[str, Any]) -> tuple[float, float]:
        """Calculate elevation gain and loss from path data"""
        elevation_gain = 0
        elevation_loss = 0

        # Try multiple ways to get elevation data from GraphHopper response
        elevations = None

        # Method 1: Check if elevation data is in points
        if "points" in path and "coordinates" in path["points"]:
            coords = path["points"]["coordinates"]
            if len(coords) > 0 and len(coords[0]) >= 3:
                # Coordinates include elevation as third dimension [lng, lat, elevation]
                elevations = [coord[2] for coord in coords if len(coord) >= 3]

        # Method 2: Check path details for elevation
        if not elevations and "details" in path:
            if "elevation" in path["details"]:
                elevation_details = path["details"]["elevation"]
                elevations = [
                    detail[2] if len(detail) >= 3 else 0 for detail in elevation_details
                ]

        # Method 3: Use ascend/descend from path if available
        if not elevations:
            if "ascend" in path and "descend" in path:
                return float(path["ascend"]), float(path["descend"])

        # Calculate from elevation points if we have them
        if elevations and len(elevations) > 1:
            for i in range(1, len(elevations)):
                diff = elevations[i] - elevations[i - 1]
                if diff > 0:
                    elevation_gain += diff
                else:
                    elevation_loss += abs(diff)

        logger.info(
            f"Calculated elevation: gain={elevation_gain:.1f}m, loss={elevation_loss:.1f}m"
        )
        return elevation_gain, elevation_loss

    def _create_route_record(
        self,
        route_data: Dict[str, Any],
        params: RouteGenerationParams,
        user_id: str,
        gh_response: Dict[str, Any],
    ) -> Route:
        """Create Route database record"""
        return Route(
            user_id=user_id,
            name=f"{params.route_type.title()} Route - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            route_type=params.route_type,
            profile=params.profile,
            geometry=route_data["geometry"],
            distance_m=route_data["distance_m"],
            total_elevation_gain_m=route_data["elevation_gain"],
            total_elevation_loss_m=route_data["elevation_loss"],
            estimated_time_s=route_data["time_ms"] // 1000,
            start_lat=route_data["start_coord"][1],
            start_lng=route_data["start_coord"][0],
            end_lat=route_data["end_coord"][1],
            end_lng=route_data["end_coord"][0],
            is_loop=params.is_loop,
            generation_params=params.dict(),
            graphhopper_response=gh_response,
        )

    def _enhance_with_strava(self, route: Route, user_id: str, db: Session) -> None:
        """Add Strava integration to route"""
        strava_data = self.strava_integration.enhance_route_with_strava_data(
            route.geometry, user_id, db
        )
        route.strava_segments = strava_data["segments"]
        route.popularity_score = strava_data["popularity_score"]

    def _calculate_difficulty(
        self, route: Route, params: RouteGenerationParams
    ) -> float:
        """Calculate route difficulty score"""
        return min(
            10.0,
            (
                (route.distance_m / 1000) * 0.5
                + (route.total_elevation_gain_m / 100) * 1.0  # Distance factor
                + (  # Elevation factor
                    2.0 if params.route_type == "mountain" else 1.0
                )  # Terrain factor
            ),
        )


# Service instance
route_generation_service = RouteGenerationService()
