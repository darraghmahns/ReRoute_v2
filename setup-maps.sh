#!/usr/bin/env bash
# setup-maps.sh — download OSM region files and merge them into a single
# routing graph for GraphHopper.
#
# Usage:
#   ./setup-maps.sh              # merge Ireland + California (default)
#   REGIONS="ireland california" ./setup-maps.sh   # same, explicit
#
# Requirements:
#   - docker  (always needed for GraphHopper)
#   - osmium-tool  (brew install osmium-tool) OR docker (used as fallback)
#
# After running this script, rebuild the GraphHopper graph:
#   ./dev.sh   (GraphHopper will auto-import the merged file on first start)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$PROJECT_ROOT/graphhopper-data"

mkdir -p "$DATA_DIR"

# ── Region definitions ────────────────────────────────────────────────────────
declare -A REGION_URLS
REGION_URLS=(
  [ireland]="https://download.geofabrik.de/europe/ireland-and-northern-ireland-latest.osm.pbf"
  [california]="https://download.geofabrik.de/north-america/us/california-latest.osm.pbf"
  [gb]="https://download.geofabrik.de/europe/great-britain-latest.osm.pbf"
  [france]="https://download.geofabrik.de/europe/france-latest.osm.pbf"
  [montana]="https://download.geofabrik.de/north-america/us/montana-latest.osm.pbf"
)

declare -A REGION_FILES
REGION_FILES=(
  [ireland]="ireland-and-northern-ireland-latest.osm.pbf"
  [california]="california-latest.osm.pbf"
  [gb]="great-britain-latest.osm.pbf"
  [france]="france-latest.osm.pbf"
  [montana]="montana-latest.osm.pbf"
)

# ── Which regions to include ──────────────────────────────────────────────────
REGIONS="${REGIONS:-ireland california}"
read -ra REGION_LIST <<< "$REGIONS"

echo "Regions: ${REGION_LIST[*]}"
echo "Data dir: $DATA_DIR"
echo ""

# ── Download missing files ────────────────────────────────────────────────────
INPUT_FILES=()

for region in "${REGION_LIST[@]}"; do
  if [[ -z "${REGION_URLS[$region]+_}" ]]; then
    echo "Error: Unknown region '$region'. Available: ${!REGION_URLS[*]}"
    exit 1
  fi

  file="$DATA_DIR/${REGION_FILES[$region]}"
  if [ -f "$file" ]; then
    size=$(du -sh "$file" | cut -f1)
    echo "✓ $region already downloaded ($size)"
  else
    url="${REGION_URLS[$region]}"
    echo "⬇ Downloading $region from $url ..."
    curl -L --progress-bar -o "$file" "$url"
    size=$(du -sh "$file" | cut -f1)
    echo "✓ $region downloaded ($size)"
  fi

  INPUT_FILES+=("$file")
done

echo ""

# ── Merge ─────────────────────────────────────────────────────────────────────
MERGED="$DATA_DIR/merged-latest.osm.pbf"

if [ "${#INPUT_FILES[@]}" -eq 1 ]; then
  # Single region — just symlink/copy, no merge needed
  echo "Only one region — copying to merged-latest.osm.pbf"
  cp "${INPUT_FILES[0]}" "$MERGED"
else
  echo "Merging ${#INPUT_FILES[@]} region files → merged-latest.osm.pbf ..."

  # Build the list as /data-relative paths for osmium inside Docker
  OSMIUM_INPUTS=()
  for f in "${INPUT_FILES[@]}"; do
    OSMIUM_INPUTS+=("/data/$(basename "$f")")
  done

  if command -v osmium &>/dev/null; then
    echo "(using local osmium-tool)"
    osmium merge "${INPUT_FILES[@]}" -o "$MERGED" --overwrite
  else
    echo "(osmium not found locally — using Docker fallback)"
    echo "Tip: brew install osmium-tool to skip the Docker pull next time"
    docker run --rm \
      -v "$DATA_DIR:/data" \
      ghcr.io/osmcode/osmium-tool \
      merge "${OSMIUM_INPUTS[@]}" -o /data/merged-latest.osm.pbf --overwrite
  fi

  size=$(du -sh "$MERGED" | cut -f1)
  echo "✓ Merged file created ($size)"
fi

echo ""

# ── Clear old graph cache ─────────────────────────────────────────────────────
CACHE_DIR="$DATA_DIR/graph-cache"
if [ -d "$CACHE_DIR" ]; then
  echo "Removing old graph cache (GraphHopper will rebuild on next start)..."
  rm -rf "$CACHE_DIR"
  echo "✓ Cache cleared"
else
  echo "No existing graph cache to clear."
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Done! Merged map ready: $(basename "$MERGED")"
echo ""
echo "Next step: run ./dev.sh"
echo "GraphHopper will build the routing graph on first start."
echo "(This takes 5–15 min for Ireland+California — go make a coffee.)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
