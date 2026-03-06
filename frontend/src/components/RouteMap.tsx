import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

// Set your Mapbox access token
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

if (MAPBOX_TOKEN) {
  mapboxgl.accessToken = MAPBOX_TOKEN;
}

interface RouteMapProps {
  onLocationSelect?: (lat: number, lng: number) => void;
  selectedLocation?: { lat: number; lng: number } | null;
  selectedWaypoint?: { lat: number; lng: number } | null;
  routeGeometry?: {
    type: 'LineString';
    coordinates: number[][];
  } | null;
  height?: string;
  interactive?: boolean;
  className?: string;
}

const RouteMap: React.FC<RouteMapProps> = ({
  onLocationSelect,
  selectedLocation,
  selectedWaypoint,
  routeGeometry,
  height = '14rem',
  interactive = true,
  className = '',
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [isMapReady, setIsMapReady] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  const markerRef = useRef<mapboxgl.Marker | null>(null);
  const waypointMarkerRef = useRef<mapboxgl.Marker | null>(null);
  const onLocationSelectRef = useRef(onLocationSelect);

  useEffect(() => {
    onLocationSelectRef.current = onLocationSelect;
  }, [onLocationSelect]);

  // Error boundary for the map
  useEffect(() => {
    if (!MAPBOX_TOKEN) {
      setMapError('Mapbox token is not configured');
      return;
    }

    if (!mapContainer.current) return;

    let isMounted = true;

    try {
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/outdoors-v12',
        center: [-110.5, 45.8], // Montana center
        zoom: 7,
        interactive,
      });

      if (interactive) {
        map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
      }

      map.current.on('load', () => {
        if (isMounted) setIsMapReady(true);
      });

      if (interactive) {
        map.current.on('click', (e) => {
          const { lng, lat } = e.lngLat;
          if (onLocationSelectRef.current) {
            onLocationSelectRef.current(lat, lng);
          }
        });
      }
    } catch {
      setMapError('Failed to load map.');
    }

    return () => {
      isMounted = false;
      map.current?.remove();
    };
  }, []); // Only run once on mount

  // Update selected location marker (as a pin)
  useEffect(() => {
    if (!map.current || !isMapReady) return;
    try {
      // Remove existing marker
      if (markerRef.current) {
        markerRef.current.remove();
        markerRef.current = null;
      }

      if (selectedLocation) {
        // Add a pin marker (draggable)
        markerRef.current = new mapboxgl.Marker({
          color: '#3B82F6',
          draggable: true,
        })
          .setLngLat([selectedLocation.lng, selectedLocation.lat])
          .addTo(map.current);

        // Pan to the selected location
        map.current.flyTo({
          center: [selectedLocation.lng, selectedLocation.lat],
          zoom: 12,
        });

        // Listen for drag end
        markerRef.current.on('dragend', () => {
          const lngLat = markerRef.current!.getLngLat();
          if (onLocationSelect) {
            onLocationSelect(lngLat.lat, lngLat.lng);
          }
        });
      }
    } catch {
      setMapError('Failed to update map marker.');
    }
  }, [selectedLocation, isMapReady]);

  // Update via-waypoint marker (green pin)
  useEffect(() => {
    if (!map.current || !isMapReady) return;
    try {
      if (waypointMarkerRef.current) {
        waypointMarkerRef.current.remove();
        waypointMarkerRef.current = null;
      }
      if (selectedWaypoint) {
        waypointMarkerRef.current = new mapboxgl.Marker({ color: '#22c55e' })
          .setLngLat([selectedWaypoint.lng, selectedWaypoint.lat])
          .addTo(map.current);
      }
    } catch {
      // non-fatal
    }
  }, [selectedWaypoint, isMapReady]);

  // Update route geometry
  useEffect(() => {
    if (!map.current || !isMapReady) return;
    try {
      // Remove existing route
      const existingRoute = map.current.getSource('route');
      if (existingRoute) {
        map.current.removeLayer('route-line');
        map.current.removeSource('route');
      }

      if (routeGeometry) {
        // Only add source/layer if style is loaded
        if (!map.current.isStyleLoaded()) return;
        map.current.addSource('route', {
          type: 'geojson',
          data: {
            type: 'Feature',
            properties: {},
            geometry: routeGeometry,
          },
        });

        map.current.addLayer({
          id: 'route-line',
          type: 'line',
          source: 'route',
          layout: {
            'line-join': 'round',
            'line-cap': 'round',
          },
          paint: {
            'line-color': '#3B82F6',
            'line-width': 3,
          },
        });

        // Fit map to route bounds
        const coordinates = routeGeometry.coordinates;
        if (coordinates.length > 0) {
          const bounds = coordinates.reduce(
            (bounds, coord) => {
              return bounds.extend(coord as [number, number]);
            },
            new mapboxgl.LngLatBounds(
              coordinates[0] as [number, number],
              coordinates[0] as [number, number]
            )
          );

          map.current.fitBounds(bounds, {
            padding: 20,
          });
        }
      }
    } catch {
      setMapError('Failed to update route geometry.');
    }
  }, [routeGeometry, isMapReady]);

  if (mapError) {
    return (
      <div
        className={`bg-red-100 flex items-center justify-center text-red-600 text-sm rounded-lg ${className}`}
        style={{ height }}
      >
        {mapError}
      </div>
    );
  }

  if (!MAPBOX_TOKEN) {
    return (
      <div
        className={`bg-gray-200 flex items-center justify-center text-gray-600 text-sm rounded-lg ${className}`}
        style={{ height }}
      >
        Mapbox token not configured
      </div>
    );
  }

  return (
    <div
      ref={mapContainer}
      className={`rounded-lg overflow-hidden ${className}`}
      style={{ height }}
    />
  );
};

export default RouteMap;
