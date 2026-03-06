import json
import logging
import math
import random
from typing import Any, Dict, List, Optional, Tuple

import requests

from app.core.config import settings
from app.schemas.route import RouteGenerationParams
from app.schemas.terrain import TerrainTarget
from app.services.overpass_service import overpass_service

logger = logging.getLogger(__name__)


class GraphHopperService:
    def __init__(self):
        self.base_url = settings.GRAPHHOPPER_BASE_URL.rstrip("/")
        self.timeout = 30

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to GraphHopper API.

        Uses POST with a JSON body when a custom_model is present — the
        serialised model can easily exceed the 8kB GET URL limit.
        Uses GET for all other requests (profile-only, isochrone, matrix).
        """
        try:
            url = f"{self.base_url}/{endpoint}"
            if "custom_model" in params and endpoint == "route":
                body = dict(params)
                # Convert custom_model from string to dict if needed
                if isinstance(body.get("custom_model"), str):
                    body["custom_model"] = json.loads(body["custom_model"])
                # GH POST /route uses "points" (array of [lng, lat]) not "point" (list of "lat,lng")
                if "point" in body:
                    pts = body.pop("point")
                    body["points"] = [
                        [float(c.split(",")[1]), float(c.split(",")[0])]
                        for c in pts
                    ]
                # Convert string booleans to real booleans for JSON body
                for key in ("points_encoded", "elevation", "instructions", "calc_points"):
                    if key in body and isinstance(body[key], str):
                        body[key] = body[key].lower() == "true"
                response = requests.post(
                    url,
                    json=body,
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout,
                )
            else:
                response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GraphHopper API error: {e}")
            raise Exception(f"GraphHopper API error: {e}")

    def generate_route(self, params: RouteGenerationParams) -> Dict[str, Any]:
        """Generate a route using GraphHopper"""

        # Convert profile to GraphHopper profile
        profile_mapping = {"bike": "bike", "gravel": "gravel", "mountain": "mountain"}

        gh_profile = profile_mapping.get(params.profile, "bike")

        # Build GraphHopper request parameters
        elevation_val = "true" if settings.GRAPHHOPPER_ELEVATION_ENABLED else "false"
        gh_params = {
            "profile": gh_profile,
            "point": [],
            "points_encoded": "false",
            "elevation": elevation_val,
            "instructions": "true",
            "calc_points": "true",
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

        # Force departure direction on the start point using GH's heading parameter.
        # One heading value per point; use -1 to leave intermediate/end points unconstrained.
        if params.start_heading is not None:
            num_points = len(gh_params["point"])
            gh_params["heading"] = [params.start_heading] + [-1] * (num_points - 1)
            logger.info(f"Departure heading set to {params.start_heading:.0f}°")

        # Add custom model parameters for route preferences.
        # Overpass pre-flight is skipped (bbox=None) — GH tag-based priority rules
        # already enforce surface/access violations via the graph's encoded values.
        # Polygon-area exclusions from Overpass routinely exceed GH's 5 MB model limit.
        custom_model = self._build_custom_model(params, bbox=None)
        if custom_model:
            gh_params["custom_model"] = json.dumps(custom_model)

        # Debug logging
        logger.info(
            f"GraphHopper request params: profile={gh_params.get('profile')}, points={gh_params.get('point')}"
        )
        if custom_model:
            logger.info(
                f"Custom model for route_type={params.route_type}: speed_rules={len(custom_model.get('speed', []))}, priority_rules={len(custom_model.get('priority', []))}"
            )
            logger.info(f"Full custom model JSON: {json.dumps(custom_model, indent=2)}")

        # Make request to GraphHopper
        return self._make_request("route", gh_params)

    def _build_custom_model(
        self,
        params: RouteGenerationParams,
        bbox: Optional[Tuple[float, float, float, float]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Build a GraphHopper custom model for route preferences.

        When params.terrain_target is set, delegates to _build_terrain_aware_model()
        which emits explicit hard-blocks for surface/access violations.

        When terrain_target is None, falls back to _build_legacy_model() which
        preserves the original gravel/MTB priority-multiplier behaviour.
        """
        if params.terrain_target is not None:
            logger.info(
                f"Building terrain-aware custom model: surface_type={params.terrain_target.surface_type}, "
                f"workout_structure={params.terrain_target.workout_structure}, "
                f"profile={params.profile}"
            )
            return self._build_terrain_aware_model(
                params.terrain_target, bbox=bbox, profile=params.profile
            )

        return self._build_legacy_model(params)

    def _build_terrain_aware_model(
        self,
        target: TerrainTarget,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        profile: str = "bike",
    ) -> Dict[str, Any]:
        """
        Build a custom model from a TerrainTarget.

        Surface and access violations are emitted as HARD BLOCKS (multiply_by: 0).
        This is deterministic — the router cannot find a route that crosses a blocked
        surface regardless of how isolated or attractive that road would otherwise be.

        When bbox is provided, also fetches Overpass area exclusions and adds them
        as polygon-based blocks in custom_model.areas. This is additive hardening —
        the tag-based blocks above are the primary enforcement mechanism.

        For mountain and gravel profiles, the GH profile JSON files (mountain.json,
        gravel.json) already encode surface preferences — so surface/highway hard-blocks
        from terrain research are skipped to avoid contradicting those files.
        """
        # Fetch Overpass exclusion zones if we have a bbox
        exclusion_features: List[Dict[str, Any]] = []
        if bbox is not None:
            exclusion_features = overpass_service.get_all_exclusions(bbox, target)
            logger.info(
                f"Overpass pre-flight: {len(exclusion_features)} exclusion features for bbox={bbox}"
            )

        model: Dict[str, Any] = {
            "speed": [],
            "priority": [],
            "areas": {"type": "FeatureCollection", "features": exclusion_features},
        }

        # Add priority rules that reference each Overpass exclusion area by id
        for feature in exclusion_features:
            feature_id = feature.get("id", "")
            if feature_id:
                model["priority"].append(
                    {"if": f"in_{feature_id}", "multiply_by": "0"}
                )

        # ── Surface hard-blocks ───────────────────────────────────────────
        # mountain/gravel profiles: skip — the GH JSON files already handle surface
        # weighting. Applying road-bike forbidden lists on top would contradict them.
        # bike profile: apply hard-blocks from terrain research as before.
        if profile == "bike" and target.surface_type != "any":
            for surface in target.forbidden_osm_surfaces:
                model["priority"].append(
                    {"if": f"surface == {surface.upper()}", "multiply_by": "0"}
                )
            for highway in target.forbidden_osm_highways:
                model["priority"].append(
                    {"if": f"road_class == {highway.upper()}", "multiply_by": "0"}
                )

        # ── Access control hard-blocks ────────────────────────────────────
        if not target.allow_private:
            model["priority"].append({"if": "road_access == PRIVATE", "multiply_by": "0"})
            model["priority"].append({"if": "road_access == NO", "multiply_by": "0"})

        # ── Promote preferred surfaces for gravel_ok (road bike only) ─────
        # gravel/mountain profiles get surface promotion from their JSON files.
        if profile == "bike" and target.surface_type == "gravel_ok":
            model["priority"].extend(
                [
                    {"if": "surface == GRAVEL", "multiply_by": "1.5"},
                    {"if": "surface == UNPAVED", "multiply_by": "1.3"},
                    {"if": "road_class == UNCLASSIFIED", "multiply_by": "1.2"},
                ]
            )

        # ── Workout flow rules ────────────────────────────────────────────
        if target.workout_structure == "interval":
            # Intervals need long uninterrupted stretches — penalise short/busy roads
            model["priority"].append(
                {"if": "road_class == LIVING_STREET", "multiply_by": "0.1"}
            )
            model["priority"].append(
                {"if": "road_class == SERVICE", "multiply_by": "0.2"}
            )
            if profile == "bike":
                # Road bike: prefer open classified roads for sustained efforts
                model["priority"].append(
                    {"if": "road_class == PRIMARY", "multiply_by": "1.2"}
                )
                model["priority"].append(
                    {"if": "road_class == SECONDARY", "multiply_by": "1.2"}
                )
            elif profile == "gravel":
                # Gravel: prefer long unclassified/secondary roads
                model["priority"].append(
                    {"if": "road_class == UNCLASSIFIED", "multiply_by": "1.2"}
                )
                model["priority"].append(
                    {"if": "road_class == SECONDARY", "multiply_by": "1.1"}
                )
            # mountain: no road class boosts — GH JSON handles preferred terrain

        elif target.workout_structure == "rolling_hills" and target.grade_range:
            min_g, max_g = target.grade_range
            # Promote segments in the target gradient window
            model["speed"].append(
                {
                    "if": f"average_slope > {min_g} && average_slope < {max_g}",
                    "multiply_by": "1.3",
                }
            )

        elif target.workout_structure == "race_simulation":
            if profile == "mountain":
                # MTB race sim: boost off-road terrain
                model["priority"].extend([
                    {"if": "road_class == TRACK", "multiply_by": "1.3"},
                    {"if": "road_class == PATH", "multiply_by": "1.2"},
                    {"if": "surface == DIRT", "multiply_by": "1.2"},
                    {"if": "surface == GRAVEL", "multiply_by": "1.1"},
                ])
            elif profile == "gravel":
                # Gravel race sim: boost gravel/unpaved surfaces
                model["priority"].extend([
                    {"if": "surface == GRAVEL", "multiply_by": "1.3"},
                    {"if": "surface == UNPAVED", "multiply_by": "1.2"},
                    {"if": "road_class == UNCLASSIFIED", "multiply_by": "1.1"},
                ])
            else:
                # Road bike race sim: prefer open classified roads
                model["priority"].append(
                    {"if": "road_class == TERTIARY", "multiply_by": "1.1"}
                )
                model["priority"].append(
                    {"if": "road_class == SECONDARY", "multiply_by": "1.2"}
                )
                model["priority"].append(
                    {"if": "road_class == PRIMARY", "multiply_by": "1.1"}
                )

        logger.info(
            f"Terrain-aware custom model: "
            f"{len(model['priority'])} priority rules, {len(model['speed'])} speed rules"
        )
        return model

    def _build_legacy_model(
        self, params: RouteGenerationParams
    ) -> Optional[Dict[str, Any]]:
        """
        Original custom model logic preserved verbatim.
        Only used when params.terrain_target is None.
        """
        # For road bikes, use the server's default bike.json profile (already blocks unpaved roads)
        if params.route_type == "road" or params.profile == "bike":
            logger.info("Using server's default bike profile (no custom model)")
            return None

        # Only use custom models for gravel and mountain bikes
        custom_model = {
            "speed": [],
            "priority": [],
            "areas": {"type": "FeatureCollection", "features": []},
        }

        if params.route_type == "gravel":
            # Gravel bike: Allow unpaved surfaces that road bikes avoid
            custom_model["priority"].extend(
                [
                    {"if": "surface == GRAVEL", "multiply_by": "1.5"},
                    {"if": "surface == UNPAVED", "multiply_by": "1.3"},
                    {"if": "road_class == UNCLASSIFIED", "multiply_by": "1.2"},
                    {
                        "if": "road_class == TRACK && surface == GRAVEL",
                        "multiply_by": "1.1",
                    },
                ]
            )

        elif params.route_type == "mountain":
            # Mountain bike: boost trail surfaces only.
            # mountain.json already penalises urban roads (RESIDENTIAL ×0.2,
            # PRIMARY ×0 speed, etc.).  Adding more road penalties here would
            # compound multiplicatively and make residential/tertiary roads
            # near-impassable (×0.02), which breaks round_trip routing — the
            # algorithm can't escape the city to reach the trail network.
            # We only add POSITIVE boosts so the profile stays navigable.
            custom_model["priority"].extend(
                [
                    {"if": "road_class == TRACK", "multiply_by": "1.5"},
                    {"if": "road_class == PATH", "multiply_by": "1.3"},
                    {"if": "surface == DIRT", "multiply_by": "1.2"},
                    {"if": "surface == GRAVEL", "multiply_by": "1.1"},
                    {"if": "surface == UNPAVED", "multiply_by": "1.15"},
                    {"if": "surface == GROUND", "multiply_by": "1.2"},
                ]
            )

        return custom_model if custom_model["priority"] else None

    def generate_loop_route(
        self,
        lat: float,
        lng: float,
        distance_km: float,
        profile: str = "bike",
        route_type: str = "road",
    ) -> Dict[str, Any]:
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
            is_loop=True,
        )

        return self.generate_route(params)

    def get_isochrone(
        self, lat: float, lng: float, time_limit: int = 1800, profile: str = "bike"
    ) -> Dict[str, Any]:
        """Get isochrone (reachable area) from a point"""

        gh_params = {
            "point": f"{lat},{lng}",
            "time_limit": time_limit,
            "profile": profile,
            "buckets": "3",
        }

        return self._make_request("isochrone", gh_params)

    def matrix_request(
        self, points: List[Tuple[float, float]], profile: str = "bike"
    ) -> Dict[str, Any]:
        """Calculate distance/time matrix between multiple points"""

        gh_params = {
            "profile": profile,
            "point": [f"{lat},{lng}" for lat, lng in points],
            "out_arrays": ["times", "distances"],
        }

        return self._make_request("matrix", gh_params)

    def health_check(self) -> bool:
        """Check if GraphHopper service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/healthcheck", timeout=5)
            return response.status_code == 200
        except:
            return False

    def _snap_to_road(
        self, lat: float, lng: float, profile: str = "bike", route_type: str = "road"
    ) -> Tuple[float, float]:
        """Snap a point to the nearest road using GraphHopper's /nearest endpoint"""
        
        # For road cycling, skip snapping to avoid dirt roads - let GraphHopper find the best paved route
        if route_type == "road":
            logger.info(f"Skipping road snapping for road route type - using exact coordinates: {lat:.6f},{lng:.6f}")
            return lat, lng
        
        try:
            url = f"{self.base_url}/nearest"
            params = {"point": f"{lat},{lng}", "profile": profile}
            response = requests.get(url, params=params, timeout=self.timeout)

            # If /nearest endpoint doesn't exist (404) or has server errors (500), return original coordinates
            if response.status_code in [404, 500]:
                logger.warning(
                    f"/nearest endpoint unavailable (status {response.status_code}), using original coordinates: {lat}, {lng}"
                )
                return lat, lng

            response.raise_for_status()
            data = response.json()
            mapped = data.get("mapped_point")
            if mapped:
                snapped_lat, snapped_lng = mapped["lat"], mapped["lon"]
                logger.debug(
                    f"Snapped {lat:.6f},{lng:.6f} to {snapped_lat:.6f},{snapped_lng:.6f}"
                )
                return snapped_lat, snapped_lng
            # fallback to input if not found
            return lat, lng
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [404, 500]:
                logger.warning(
                    f"/nearest endpoint error (status {e.response.status_code}), using original coordinates: {lat}, {lng}"
                )
                return lat, lng
            else:
                logger.error(f"HTTP error snapping to road: {e}")
                return lat, lng
        except Exception as e:
            logger.error(f"Error snapping to road: {e}")
            return lat, lng

    def _generate_loop_waypoints(
        self,
        start_lat: float,
        start_lng: float,
        num_points: int,
        radius_m: float,
        profile: str = "bike",
    ) -> List[Dict[str, float]]:
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
            radius_variation = random.uniform(
                0.8, 1.2
            )  # 20% radius variation (less extreme)
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

    def _generate_conservative_waypoints(
        self,
        start_lat: float,
        start_lng: float,
        num_points: int,
        radius_m: float,
        profile: str = "bike",
    ) -> List[Dict[str, float]]:
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

    def generate_ai_loop_route(
        self,
        start_lat: float,
        start_lng: float,
        distance_km: float,
        profile: str = "bike",
        route_type: str = "road",
        num_waypoints: int = 3,
        terrain_target: Optional["TerrainTarget"] = None,
        via_lat: Optional[float] = None,
        via_lng: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Generate a loop route using GraphHopper's round_trip algorithm.

        When via_lat/via_lng are provided the round_trip algorithm is bypassed
        and the route is forced through the user-specified point instead.

        Uses algorithm=round_trip with randomised seeds across attempts so each
        retry explores a different part of the trail network.  The custom model
        (mountain/gravel surface preferences) is applied to every attempt.
        """
        try:
            target_distance_m = int(distance_km * 1000)
            tolerance = 0.20  # 20% — round_trip distance is approximate
            max_attempts = 5

            best_route = None
            best_distance_diff = float("inf")

            logger.info(
                f"Targeting {distance_km:.1f}km loop from {start_lat:.4f},{start_lng:.4f} (profile={profile})"
            )

            from app.schemas.route import RouteGenerationParams, RouteWaypointCreate

            # ── User-provided via waypoint: force route through specific point ──
            if via_lat is not None and via_lng is not None:
                logger.info(
                    f"Using user-provided via waypoint at {via_lat:.4f},{via_lng:.4f}"
                )
                params = RouteGenerationParams(
                    start_lat=start_lat,
                    start_lng=start_lng,
                    profile=profile,
                    route_type=route_type,
                    distance_km=distance_km,
                    is_loop=True,
                    waypoints=[
                        RouteWaypointCreate(
                            lat=via_lat, lng=via_lng, waypoint_type="via"
                        )
                    ],
                    terrain_target=terrain_target,
                )
                return self.generate_route(params)
            # ──────────────────────────────────────────────────────────────────

            # For mountain profile: shift the round_trip start to a point in the
            # mountain trail network north of the user's location.  Starting from
            # a city centre produces poor loops because the algorithm stays on
            # residential roads — it never "knows" to go north into the mountains.
            #
            # We gather N candidate starting points via Overpass (all ±45° north)
            # spaced across the available distance range, plus a geometric fallback.
            # round_trip is tried from each; the route closest to the target wins.
            candidate_starts: List[Tuple[float, float]] = [(start_lat, start_lng)]
            if profile == "mountain":
                ideal_dist_m = max(4000, target_distance_m // 3)

                # Multi-candidate Overpass query (one request, N evenly-spaced nodes)
                overpass_candidates: List[Tuple[float, float]] = []
                try:
                    overpass_candidates = overpass_service.find_mountain_trail_candidates(
                        start_lat, start_lng,
                        radius_m=15000,
                        min_dist_m=3000,
                        n_candidates=4,  # 2 per bearing wing (NNE + NNW)
                    )
                    if overpass_candidates:
                        logger.info(
                            f"Mountain: {len(overpass_candidates)} Overpass candidates: "
                            + ", ".join(f"({la:.4f},{lo:.4f})" for la, lo in overpass_candidates)
                        )
                    else:
                        logger.info("Mountain: Overpass returned no northward trail candidates")
                except Exception as exc:
                    logger.warning(f"Overpass trailhead query failed: {exc}")

                # Geometric fallback: project ideal_dist_m due north
                delta_lat = ideal_dist_m / 111_111
                geo_start = (start_lat + delta_lat, start_lng)

                # Use Overpass candidates first (prefer real trail access points),
                # then append the geometric fallback for coverage.
                candidate_starts = overpass_candidates or []
                if geo_start not in candidate_starts:
                    candidate_starts.append(geo_start)
                    logger.info(
                        f"Mountain: geometric fallback ({geo_start[0]:.5f},{geo_start[1]:.5f}) "
                        f"{ideal_dist_m//1000}km north"
                    )

            # Build custom model (same for all starting points and seeds)
            dummy_params = RouteGenerationParams(
                start_lat=candidate_starts[0][0],
                start_lng=candidate_starts[0][1],
                profile=profile,
                route_type=route_type,
                distance_km=distance_km,
                is_loop=True,
                terrain_target=terrain_target,
            )
            custom_model = self._build_custom_model(dummy_params, bbox=None)

            elevation_enabled = bool(getattr(settings, "GRAPHHOPPER_ELEVATION_ENABLED", True))
            url = f"{self.base_url}/route"

            attempt = 0
            seeds = [random.randint(0, 99999) for _ in range(3)]
            for rt_start_lat, rt_start_lng in candidate_starts:
                for seed in seeds[:max(2, max_attempts // len(candidate_starts))]:
                    attempt += 1
                    try:
                        body: Dict[str, Any] = {
                            "profile": profile,
                            # POST /route expects [[lng, lat]] — note longitude first
                            "points": [[rt_start_lng, rt_start_lat]],
                            "algorithm": "round_trip",
                            "round_trip": {
                                "distance": target_distance_m,
                                "points": num_waypoints,
                                "seed": seed,
                            },
                            "points_encoded": False,
                            "elevation": elevation_enabled,
                            "instructions": True,
                            "calc_points": True,
                        }

                        if custom_model:
                            body["custom_model"] = custom_model

                        logger.info(
                            f"Round-trip attempt {attempt}: "
                            f"start=({rt_start_lat:.4f},{rt_start_lng:.4f}), "
                            f"distance={distance_km:.1f}km, seed={seed}, profile={profile}"
                        )

                        response = requests.post(
                            url,
                            json=body,
                            headers={"Content-Type": "application/json"},
                            timeout=self.timeout,
                        )
                        response.raise_for_status()
                        data = response.json()

                        if "paths" in data and data["paths"]:
                            actual_m = data["paths"][0]["distance"]
                            actual_km = actual_m / 1000
                            diff = abs(actual_m - target_distance_m)
                            ratio = diff / target_distance_m

                            logger.info(
                                f"Round-trip attempt {attempt}: {actual_km:.1f}km "
                                f"(target {distance_km:.1f}km, diff={ratio:.1%})"
                            )

                            if ratio <= tolerance:
                                logger.info(f"Found good route on attempt {attempt}!")
                                return data

                            if diff < best_distance_diff:
                                best_distance_diff = diff
                                best_route = data
                                logger.info(f"New best: {actual_km:.1f}km")

                    except Exception as e:
                        logger.warning(f"Round-trip attempt {attempt} failed: {e}")
                        continue

            if best_route:
                actual_km = best_route["paths"][0]["distance"] / 1000
                logger.info(
                    f"Returning best route: target={distance_km:.1f}km actual={actual_km:.1f}km"
                )
                return best_route

            raise Exception("All round-trip route generation attempts failed")

        except Exception as e:
            logger.error(f"AI loop route generation failed: {e}")
            raise

    def _get_waypoint_at_distance(
        self,
        start_lat: float,
        start_lng: float,
        distance_km: float,
        bearing_degrees: float,
    ) -> tuple[float, float]:
        """Calculate lat/lng of a point at given distance and bearing from start point"""
        R = 6378137  # Earth radius in meters
        distance_m = distance_km * 1000

        bearing_rad = math.radians(bearing_degrees)
        lat1_rad = math.radians(start_lat)
        lng1_rad = math.radians(start_lng)

        lat2_rad = math.asin(
            math.sin(lat1_rad) * math.cos(distance_m / R)
            + math.cos(lat1_rad) * math.sin(distance_m / R) * math.cos(bearing_rad)
        )

        lng2_rad = lng1_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(distance_m / R) * math.cos(lat1_rad),
            math.cos(distance_m / R) - math.sin(lat1_rad) * math.sin(lat2_rad),
        )

        return math.degrees(lat2_rad), math.degrees(lng2_rad)


    def _bbox_around_point(
        self, lat: float, lng: float, radius_km: float
    ) -> Tuple[float, float, float, float]:
        """
        Return a (south, west, north, east) bounding box of roughly radius_km
        around the given point. Used to scope Overpass queries.
        """
        R = 6378.137  # Earth radius in km
        delta_lat = radius_km / R * (180 / math.pi)
        delta_lng = radius_km / (R * math.cos(math.pi * lat / 180)) * (180 / math.pi)
        return (
            lat - delta_lat,
            lng - delta_lng,
            lat + delta_lat,
            lng + delta_lng,
        )


# Service instance
graphhopper_service = GraphHopperService()
