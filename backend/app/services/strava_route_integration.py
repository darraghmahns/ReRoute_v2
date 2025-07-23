import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests
from geopy.distance import geodesic
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.strava import StravaActivity
from app.models.user import Profile

logger = logging.getLogger(__name__)


class StravaRouteIntegration:
    def __init__(self):
        self.strava_api_base = "https://www.strava.com/api/v3"

    def get_user_popular_segments(
        self, user_id: str, db: Session, lat: float, lng: float, radius_km: float = 50
    ) -> List[Dict[str, Any]]:
        """Get popular segments near a location based on user's Strava data"""

        # Get user's Strava token
        profile = db.query(Profile).filter(Profile.id == user_id).first()
        if not profile or not profile.strava_access_token:
            return []

        headers = {"Authorization": f"Bearer {profile.strava_access_token}"}

        # Get segments explorer data
        segments_url = f"{self.strava_api_base}/segments/explore"
        params = {
            "bounds": self._get_bounds(lat, lng, radius_km),
            "activity_type": "cycling",
            "min_cat": 0,
            "max_cat": 5,
        }

        try:
            response = requests.get(segments_url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                return self._process_segments(data.get("segments", []))
        except Exception as e:
            logger.error(f"Error fetching Strava segments: {e}")

        return []

    def get_user_activity_heatmap_data(
        self, user_id: str, db: Session
    ) -> Dict[str, Any]:
        """Analyze user's activity data to find popular routes/areas"""

        # Get user's cached activities with GPS data
        activities = (
            db.query(StravaActivity).filter(StravaActivity.user_id == user_id).all()
        )

        if not activities:
            return {}

        heatmap_data = {
            "popular_areas": [],
            "preferred_routes": [],
            "activity_density": {},
        }

        coordinate_frequency = {}

        for activity in activities:
            if activity.streams and "latlng" in activity.streams:
                latlng_data = activity.streams["latlng"]["data"]

                # Sample coordinates to avoid too much data
                sampled_coords = latlng_data[::10]  # Every 10th point

                for coord in sampled_coords:
                    if len(coord) == 2:
                        lat, lng = coord
                        # Round to create grid cells
                        grid_lat = round(lat, 3)
                        grid_lng = round(lng, 3)
                        key = f"{grid_lat},{grid_lng}"

                        coordinate_frequency[key] = coordinate_frequency.get(key, 0) + 1

        # Find most popular areas
        sorted_areas = sorted(
            coordinate_frequency.items(), key=lambda x: x[1], reverse=True
        )

        for area, frequency in sorted_areas[:50]:  # Top 50 areas
            lat, lng = map(float, area.split(","))
            heatmap_data["popular_areas"].append(
                {
                    "lat": lat,
                    "lng": lng,
                    "frequency": frequency,
                    "popularity_score": frequency / max(coordinate_frequency.values()),
                }
            )

        return heatmap_data

    def enhance_route_with_strava_data(
        self, route_geometry: Dict[str, Any], user_id: str, db: Session
    ) -> Dict[str, Any]:
        """Enhance a route with Strava segment and popularity data"""

        if not route_geometry or route_geometry.get("type") != "LineString":
            return {"segments": [], "popularity_score": 0.0}

        coordinates = route_geometry["coordinates"]

        # Get segments along the route
        segments = []
        total_popularity = 0.0

        # Sample route coordinates
        sampled_coords = coordinates[:: max(1, len(coordinates) // 20)]  # Max 20 points

        for coord in sampled_coords:
            lng, lat = coord[:2]  # GeoJSON is [lng, lat]

            # Get segments near this point
            nearby_segments = self.get_user_popular_segments(user_id, db, lat, lng, 5)

            for segment in nearby_segments:
                # Check if segment intersects with route
                if self._segment_intersects_route(segment, coordinates):
                    segments.append(segment)
                    total_popularity += segment.get("popularity_score", 0)

        # Calculate overall popularity score
        popularity_score = (
            total_popularity / len(sampled_coords) if sampled_coords else 0.0
        )

        return {
            "segments": segments,
            "popularity_score": min(popularity_score, 1.0),  # Cap at 1.0
        }

    def suggest_route_modifications(
        self, route_geometry: Dict[str, Any], user_id: str, db: Session
    ) -> List[Dict[str, Any]]:
        """Suggest modifications to make route more popular/interesting"""

        suggestions = []

        # Get user's heatmap data
        heatmap_data = self.get_user_activity_heatmap_data(user_id, db)
        popular_areas = heatmap_data.get("popular_areas", [])

        if not popular_areas:
            return suggestions

        # Find popular areas near the route
        route_coords = route_geometry.get("coordinates", [])

        for area in popular_areas[:10]:  # Top 10 popular areas
            area_lat, area_lng = area["lat"], area["lng"]

            # Find closest point on route
            min_distance = float("inf")
            closest_route_point = None

            for coord in route_coords:
                lng, lat = coord[:2]
                distance = geodesic((lat, lng), (area_lat, area_lng)).kilometers

                if distance < min_distance:
                    min_distance = distance
                    closest_route_point = (lat, lng)

            # If popular area is reasonably close, suggest as waypoint
            if min_distance < 5:  # Within 5km
                suggestions.append(
                    {
                        "type": "waypoint",
                        "lat": area_lat,
                        "lng": area_lng,
                        "reason": f"Popular area from your activities (visited {area['frequency']} times)",
                        "distance_km": min_distance,
                        "popularity_score": area["popularity_score"],
                    }
                )

        return suggestions

    def _get_bounds(self, lat: float, lng: float, radius_km: float) -> str:
        """Get bounds string for Strava API"""
        # Simple approximation for bounds
        lat_delta = radius_km / 111  # Rough km to degree conversion
        lng_delta = radius_km / (111 * np.cos(np.radians(lat)))

        south_west = f"{lat - lat_delta},{lng - lng_delta}"
        north_east = f"{lat + lat_delta},{lng + lng_delta}"

        return f"{south_west},{north_east}"

    def _process_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and rank segments"""
        processed = []

        for segment in segments:
            processed.append(
                {
                    "id": segment.get("id"),
                    "name": segment.get("name"),
                    "distance_m": segment.get("distance"),
                    "average_grade": segment.get("avg_grade"),
                    "elevation_high": segment.get("elev_high"),
                    "elevation_low": segment.get("elev_low"),
                    "start_latlng": segment.get("start_latlng"),
                    "end_latlng": segment.get("end_latlng"),
                    "climb_category": segment.get("climb_category"),
                    "city": segment.get("city"),
                    "state": segment.get("state"),
                    "starred": segment.get("starred", False),
                    "popularity_score": min(
                        segment.get("effort_count", 0) / 1000, 1.0
                    ),  # Normalize
                }
            )

        # Sort by popularity
        processed.sort(key=lambda x: x["popularity_score"], reverse=True)

        return processed

    def _segment_intersects_route(
        self, segment: Dict[str, Any], route_coords: List[List[float]]
    ) -> bool:
        """Check if segment intersects with route (simplified)"""

        segment_start = segment.get("start_latlng")
        segment_end = segment.get("end_latlng")

        if not segment_start or not segment_end:
            return False

        # Check if segment endpoints are close to route
        threshold_km = 0.5  # 500m threshold

        for coord in route_coords[::10]:  # Sample route coordinates
            lng, lat = coord[:2]

            # Check distance to segment start
            start_dist = geodesic((lat, lng), tuple(segment_start)).kilometers
            end_dist = geodesic((lat, lng), tuple(segment_end)).kilometers

            if start_dist < threshold_km or end_dist < threshold_km:
                return True

        return False


# Service instance
strava_route_integration = StravaRouteIntegration()
