"""
Overpass API service for road surface pre-flight queries.

Provides deterministic exclusion zone data for the GraphHopper custom model.
When a bbox query returns forbidden ways (unpaved roads, private roads),
those ways are converted to GeoJSON polygon features that can be referenced
as areas in GraphHopper's custom model priority rules.

Failure mode: Overpass timeouts or errors return an empty exclusion list and
log a warning. Route generation continues without exclusions rather than failing —
the GraphHopper custom model's tag-based blocks still apply; the area-based blocks
are additive hardening.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

import requests

from app.core.config import settings
from app.schemas.terrain import TerrainTarget

logger = logging.getLogger(__name__)

# Surface tags that constitute a forbidden road for paved_only routing
_PAVED_ONLY_FORBIDDEN_SURFACES = (
    "gravel|unpaved|dirt|grass|mud|sand|ground|fine_gravel|compacted|pebblestone"
)
_ROAD_BIKE_FORBIDDEN_HIGHWAYS = "track|path|bridleway|footway|steps|cycleway"

BboxType = Tuple[float, float, float, float]  # (south, west, north, east)


class OverpassService:
    """
    Queries the Overpass API to find forbidden ways within a bounding box
    and returns them as GeoJSON features suitable for GraphHopper custom_model.areas.
    """

    def __init__(self) -> None:
        self.url = settings.OVERPASS_URL
        self.timeout = settings.OVERPASS_TIMEOUT_S

    # ── Public interface ──────────────────────────────────────────────────────

    def get_surface_exclusions(
        self, bbox: BboxType, target: TerrainTarget
    ) -> List[Dict[str, Any]]:
        """
        Return GeoJSON features of ways that violate the surface_type constraint.

        Returns an empty list if the query fails or times out — callers should
        treat an empty list as "no area-based exclusions available" (tag-based
        blocks in the custom model still apply).
        """
        if target.surface_type == "any":
            return []

        south, west, north, east = bbox
        bbox_str = f"{south},{west},{north},{east}"

        queries: List[str] = []

        if target.surface_type in ("paved_only", "paved_preferred"):
            queries.append(
                f'way[highway][surface~"^({_PAVED_ONLY_FORBIDDEN_SURFACES})$"]({bbox_str});'
            )
            queries.append(
                f'way[highway~"^({_ROAD_BIKE_FORBIDDEN_HIGHWAYS})$"]({bbox_str});'
            )

        if not queries:
            return []

        return self._run_query(queries, feature_id_prefix="surface_excl")

    def get_private_road_exclusions(self, bbox: BboxType) -> List[Dict[str, Any]]:
        """
        Return GeoJSON features of private/no-exit ways within the bbox.
        """
        south, west, north, east = bbox
        bbox_str = f"{south},{west},{north},{east}"

        queries = [
            f'way[access~"^(private|no)$"]({bbox_str});',
            f"way[noexit=yes]({bbox_str});",
        ]

        return self._run_query(queries, feature_id_prefix="access_excl")

    def find_nearest_mountain_trail_start(
        self,
        lat: float,
        lng: float,
        radius_m: int = 15000,
        min_dist_m: int = 2000,
        ideal_dist_m: Optional[int] = None,
    ) -> Optional[Tuple[float, float]]:
        """
        Find a mountain trail access node within radius_m.

        Strategy:
        1. Try explicit trailhead/guidepost nodes first.
        2. Fall back to track/path nodes filtered by bearing (±45° of north to avoid
           east/west detours) and at least min_dist_m from start.
        3. Among those, prefer nodes closest to ideal_dist_m if provided,
           otherwise pick the nearest qualifying node.
        4. If no northward (±45°) nodes found, widen to ±90° then any direction.

        Returns (lat, lng) or None on failure.
        """
        import math

        def _dist(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
            dlat = math.radians(b_lat - a_lat)
            dlng = math.radians(b_lng - a_lng)
            a = (math.sin(dlat / 2) ** 2
                 + math.cos(math.radians(a_lat))
                 * math.cos(math.radians(b_lat))
                 * math.sin(dlng / 2) ** 2)
            return 6371000 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # --- Pass 1: explicit trailhead/guidepost nodes ---
        node_query = f"""
[out:json][timeout:10];
(
  node[leisure=trailhead](around:{radius_m},{lat},{lng});
  node[tourism=trailhead](around:{radius_m},{lat},{lng});
  node[information=guidepost][sport~"cycling|mtb"](around:{radius_m},{lat},{lng});
);
out center;
"""
        try:
            resp = requests.post(self.url, data={"data": node_query}, timeout=12)
            resp.raise_for_status()
            node_elements = resp.json().get("elements", [])
        except Exception as exc:
            logger.warning(f"Trailhead node query failed: {exc}")
            node_elements = []

        if node_elements:
            # Filter to nodes beyond min_dist_m (city paths too close are excluded)
            far_nodes = [
                e for e in node_elements
                if _dist(lat, lng, e.get("lat", lat), e.get("lon", lng)) >= min_dist_m
            ]
            if far_nodes:
                best = min(
                    far_nodes,
                    key=lambda e: _dist(lat, lng, e.get("lat", lat), e.get("lon", lng)),
                )
                t_lat, t_lng = best.get("lat"), best.get("lon")
                if t_lat and t_lng:
                    d = _dist(lat, lng, t_lat, t_lng)
                    logger.info(
                        f"Trailhead node ({t_lat:.5f},{t_lng:.5f}) "
                        f"{d/1000:.1f}km from start, "
                        f"name={best.get('tags', {}).get('name', 'unnamed')}"
                    )
                    return t_lat, t_lng

        # --- Pass 2: nearest trail NODE (endpoint) via geometry query ---
        # Fetch full geometry so we can find the actual node on each trail that
        # is closest to the user's start — this gives a real trail access point
        # rather than the geographic centre of a possibly long trail.
        way_query = f"""
[out:json][timeout:20];
(
  way[highway=track](around:{radius_m},{lat},{lng});
  way[highway=path][bicycle!=no](around:{radius_m},{lat},{lng});
);
out geom;
"""
        try:
            resp = requests.post(self.url, data={"data": way_query}, timeout=25)
            resp.raise_for_status()
            way_elements = resp.json().get("elements", [])
        except Exception as exc:
            logger.warning(f"Trail way query failed: {exc}")
            return None

        if not way_elements:
            logger.info("No mountain trail ways found within radius")
            return None

        def _bearing(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
            """Compute compass bearing (0=N, 90=E, 180=S, 270=W) from A to B."""
            import math as _math
            dlng = _math.radians(b_lng - a_lng)
            x = _math.cos(_math.radians(b_lat)) * _math.sin(dlng)
            y = (_math.cos(_math.radians(a_lat)) * _math.sin(_math.radians(b_lat))
                 - _math.sin(_math.radians(a_lat)) * _math.cos(_math.radians(b_lat))
                 * _math.cos(dlng))
            return (_math.degrees(_math.atan2(x, y)) + 360) % 360

        # Collect ALL nodes from ALL trail ways (deduplicate by rounded coords)
        all_candidates: list = []
        seen_coords: set = set()
        for e in way_elements:
            tags = e.get("tags", {})
            for node in e.get("geometry", []):
                n_lat = node.get("lat")
                n_lng = node.get("lon")
                if n_lat is None or n_lng is None:
                    continue
                key = (round(n_lat, 5), round(n_lng, 5))
                if key in seen_coords:
                    continue
                seen_coords.add(key)
                d_node = _dist(lat, lng, n_lat, n_lng)
                if d_node >= min_dist_m:
                    b = _bearing(lat, lng, n_lat, n_lng)
                    all_candidates.append((d_node, n_lat, n_lng, tags, b))

        if not all_candidates:
            logger.info("No mountain trail nodes found beyond min_dist_m")
            return None

        # Filter by bearing: prefer ±45° of north, widen if needed.
        # This avoids eastward/westward nodes that are barely north (e.g. bearing=89°).
        north_tight = [c for c in all_candidates if c[4] <= 45 or c[4] >= 315]
        north_wide  = [c for c in all_candidates if c[4] <= 90 or c[4] >= 270]
        pool = north_tight or north_wide or all_candidates
        direction_label = (
            "north ±45°" if north_tight
            else "north ±90°" if north_wide
            else "any direction"
        )

        # Pick node: if ideal_dist_m given, choose node closest to that distance;
        # otherwise choose the nearest qualifying node.
        if ideal_dist_m is not None:
            best = min(pool, key=lambda c: abs(c[0] - ideal_dist_m))
        else:
            best = min(pool, key=lambda c: c[0])

        _, t_lat, t_lng, best_tags, best_bearing = best
        logger.info(
            f"Mountain trail node ({t_lat:.5f},{t_lng:.5f}) "
            f"{best[0]/1000:.1f}km from start "
            f"(bearing={best_bearing:.0f}°, {direction_label}, "
            f"ideal={ideal_dist_m//1000 if ideal_dist_m else 'nearest'}km), "
            f"name={best_tags.get('name', 'unnamed')}, highway={best_tags.get('highway', '?')}"
        )
        return t_lat, t_lng

    def find_mountain_trail_candidates(
        self,
        lat: float,
        lng: float,
        radius_m: int = 15000,
        min_dist_m: int = 3000,
        n_candidates: int = 4,
    ) -> List[Tuple[float, float]]:
        """
        Return up to n_candidates mountain trail starting points drawn from both
        the NNE (0–45°) and NNW (315–360°) sub-corridors of the northward cone.

        Splitting by bearing wing before distance-bucketing ensures that nodes
        at similar distances but different azimuths are both selected.  This is
        critical because NNE nodes (Rattlesnake drainage) and NNW nodes (Pattee
        Canyon / Stuart Peak) produce very different GraphHopper round_trip
        distances even when they sit the same number of kilometres from the user.

        Within each wing, n_candidates//2 nodes are chosen by equal-width
        distance bucketing (nearest node per bucket).  The wings are then
        interleaved: NNE-1, NNW-1, NNE-2, NNW-2, …

        Uses a single Overpass way geometry query.  Returns [] on failure
        (caller falls back to geometric north projection).
        """
        import math

        def _dist(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
            dlat = math.radians(b_lat - a_lat)
            dlng = math.radians(b_lng - a_lng)
            a = (math.sin(dlat / 2) ** 2
                 + math.cos(math.radians(a_lat)) * math.cos(math.radians(b_lat))
                 * math.sin(dlng / 2) ** 2)
            return 6371000 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        def _bearing(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
            dlng = math.radians(b_lng - a_lng)
            x = math.cos(math.radians(b_lat)) * math.sin(dlng)
            y = (math.cos(math.radians(a_lat)) * math.sin(math.radians(b_lat))
                 - math.sin(math.radians(a_lat)) * math.cos(math.radians(b_lat))
                 * math.cos(dlng))
            return (math.degrees(math.atan2(x, y)) + 360) % 360

        way_query = f"""
[out:json][timeout:20];
(
  way[highway=track](around:{radius_m},{lat},{lng});
  way[highway=path][bicycle!=no](around:{radius_m},{lat},{lng});
);
out geom;
"""
        try:
            resp = requests.post(self.url, data={"data": way_query}, timeout=25)
            resp.raise_for_status()
            way_elements = resp.json().get("elements", [])
        except Exception as exc:
            logger.warning(f"Mountain trail candidates query failed: {exc}")
            return []

        if not way_elements:
            return []

        # Collect deduplicated nodes split into NNE and NNW bearing wings.
        seen: set = set()
        nne_nodes: list = []  # bearing  0–45°  (NNE: slightly east of north)
        nnw_nodes: list = []  # bearing 315–360° (NNW: slightly west of north)
        for e in way_elements:
            for node in e.get("geometry", []):
                n_lat = node.get("lat")
                n_lng = node.get("lon")
                if n_lat is None or n_lng is None:
                    continue
                key = (round(n_lat, 4), round(n_lng, 4))
                if key in seen:
                    continue
                seen.add(key)
                d = _dist(lat, lng, n_lat, n_lng)
                if d < min_dist_m:
                    continue
                b = _bearing(lat, lng, n_lat, n_lng)
                if b <= 45:
                    nne_nodes.append((d, n_lat, n_lng))
                elif b >= 315:
                    nnw_nodes.append((d, n_lat, n_lng))

        if not nne_nodes and not nnw_nodes:
            logger.info("No northward trail candidates found for multi-candidate selection")
            return []

        def _pick_from_wing(
            wing: list, n: int
        ) -> List[Tuple[float, float]]:
            """Pick n distance-spaced nodes from a bearing wing."""
            if not wing:
                return []
            wing.sort()
            if n <= 1 or len(wing) == 1:
                return [(wing[0][1], wing[0][2])]
            max_d = wing[-1][0]
            bucket_size = (max_d - min_dist_m) / n
            picks: List[Tuple[float, float]] = []
            for i in range(n):
                lo = min_dist_m + i * bucket_size
                hi = lo + bucket_size
                bucket = [(d, la, lo2) for d, la, lo2 in wing if lo <= d < hi]
                if bucket:
                    _, b_lat, b_lng = min(bucket, key=lambda c: c[0])
                    picks.append((b_lat, b_lng))
            return picks

        n_per_wing = max(1, n_candidates // 2)
        nne_picks = _pick_from_wing(nne_nodes, n_per_wing)
        nnw_picks = _pick_from_wing(nnw_nodes, n_per_wing)

        # Interleave wings: NNE-1, NNW-1, NNE-2, NNW-2, …
        candidates: List[Tuple[float, float]] = []
        for i in range(max(len(nne_picks), len(nnw_picks))):
            if i < len(nne_picks):
                candidates.append(nne_picks[i])
            if i < len(nnw_picks):
                candidates.append(nnw_picks[i])

        all_nodes = nne_nodes + nnw_nodes
        all_nodes.sort()
        logger.info(
            f"Mountain trail candidates: {len(candidates)} nodes "
            f"(NNE={len(nne_picks)}, NNW={len(nnw_picks)}, "
            f"dist range {all_nodes[0][0]/1000:.1f}–{all_nodes[-1][0]/1000:.1f}km northward)"
        )
        return candidates

    def get_all_exclusions(
        self, bbox: BboxType, target: TerrainTarget
    ) -> List[Dict[str, Any]]:
        """
        Convenience method: return all exclusion features relevant to a TerrainTarget.
        Surface exclusions + access exclusions (when allow_private=False).
        """
        features: List[Dict[str, Any]] = []
        features.extend(self.get_surface_exclusions(bbox, target))
        if not target.allow_private:
            features.extend(self.get_private_road_exclusions(bbox))
        return features

    # ── Query builder ─────────────────────────────────────────────────────────

    def build_overpass_query(self, way_queries: List[str]) -> str:
        """
        Build a complete Overpass QL query from a list of way sub-queries.
        Returns geometry so we can extract bounding boxes for area polygons.
        """
        union_body = "\n  ".join(way_queries)
        return f"[out:json][timeout:{self.timeout}];\n(\n  {union_body}\n);\nout geom;"

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _run_query(
        self, way_queries: List[str], feature_id_prefix: str
    ) -> List[Dict[str, Any]]:
        """
        Execute an Overpass query and convert results to GeoJSON features.
        Returns an empty list on any error.
        """
        query = self.build_overpass_query(way_queries)

        try:
            response = requests.post(
                self.url,
                data={"data": query},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.Timeout:
            logger.warning(
                f"Overpass query timed out after {self.timeout}s — "
                "continuing without area-based exclusions"
            )
            return []
        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 429:
                logger.warning("Overpass rate-limited (429) — skipping area exclusions")
            else:
                logger.warning(f"Overpass HTTP error: {exc} — skipping area exclusions")
            return []
        except Exception as exc:
            logger.warning(f"Overpass query failed: {exc} — skipping area exclusions")
            return []

        return self._elements_to_geojson_features(
            data.get("elements", []), feature_id_prefix
        )

    def _elements_to_geojson_features(
        self, elements: List[Dict[str, Any]], id_prefix: str
    ) -> List[Dict[str, Any]]:
        """
        Convert Overpass way elements to GeoJSON Polygon features.

        Each way becomes a rectangular bounding-box polygon — this is sufficient
        for GraphHopper's area-based exclusion rules and avoids complex polygon
        construction from potentially incomplete node data.

        Malformed or geometry-free elements are skipped with a debug log.
        """
        features: List[Dict[str, Any]] = []

        for element in elements:
            if element.get("type") != "way":
                continue

            feature = self._way_to_bbox_feature(element, id_prefix)
            if feature is not None:
                features.append(feature)

        logger.debug(
            f"Overpass: converted {len(features)}/{len(elements)} elements to GeoJSON features"
        )
        return features

    def _way_to_bbox_feature(
        self, element: Dict[str, Any], id_prefix: str
    ) -> Optional[Dict[str, Any]]:
        """
        Build a GeoJSON Polygon feature from a way's bounding box.
        Returns None if the element has no usable geometry.
        """
        # Prefer 'geometry' array (out geom format), fall back to 'bounds'
        geometry = element.get("geometry")
        bounds = element.get("bounds")

        if geometry and len(geometry) >= 2:
            lats = [pt["lat"] for pt in geometry if "lat" in pt and "lon" in pt]
            lons = [pt["lon"] for pt in geometry if "lat" in pt and "lon" in pt]
            if not lats:
                logger.debug(f"Way {element.get('id')} has empty geometry — skipping")
                return None
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
        elif bounds:
            min_lat = bounds.get("minlat")
            max_lat = bounds.get("maxlat")
            min_lon = bounds.get("minlon")
            max_lon = bounds.get("maxlon")
            if None in (min_lat, max_lat, min_lon, max_lon):
                logger.debug(f"Way {element.get('id')} has incomplete bounds — skipping")
                return None
        else:
            logger.debug(f"Way {element.get('id')} has no geometry or bounds — skipping")
            return None

        # Add a small buffer (0.0001° ≈ 11m) so narrow roads still form a valid polygon
        buf = 0.0001
        feature_id = f"{id_prefix}_{element.get('id', 'unknown')}"
        return {
            "type": "Feature",
            "id": feature_id,
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [min_lon - buf, min_lat - buf],
                        [max_lon + buf, min_lat - buf],
                        [max_lon + buf, max_lat + buf],
                        [min_lon - buf, max_lat + buf],
                        [min_lon - buf, min_lat - buf],
                    ]
                ],
            },
            "properties": {
                "osm_id": element.get("id"),
                "tags": element.get("tags", {}),
            },
        }


# Service instance
overpass_service = OverpassService()
