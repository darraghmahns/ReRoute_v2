// Add type declaration for @mapbox/polyline if not present
// declare module '@mapbox/polyline';

import React, { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import polyline from '@mapbox/polyline';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;

if (MAPBOX_TOKEN) {
  mapboxgl.accessToken = MAPBOX_TOKEN;
}

interface MapboxActivityMapProps {
  summary_polyline: string;
  height?: number;
}

const MapboxActivityMap: React.FC<MapboxActivityMapProps> = ({
  summary_polyline,
  height = 180,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  // Check for Mapbox token
  if (!MAPBOX_TOKEN) {
    return (
      <div 
        className="bg-gray-800 border border-gray-600 rounded-lg flex items-center justify-center text-gray-400 text-sm"
        style={{ height: `${height}px` }}
      >
        Mapbox token not configured
      </div>
    );
  }

  useEffect(() => {
    if (!summary_polyline || !mapContainer.current) return;

    // Decode polyline to [lat, lng] pairs
    const coordinates: [number, number][] = polyline
      .decode(summary_polyline)
      .map(([lat, lng]: [number, number]) => [lng, lat]);

    // Center the map on the route
    const bounds = coordinates.reduce(
      (b: mapboxgl.LngLatBounds, coord: [number, number]) => b.extend(coord),
      new mapboxgl.LngLatBounds(coordinates[0], coordinates[0])
    );

    // Initialize map
    mapRef.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v11',
      bounds: bounds,
      fitBoundsOptions: { padding: 20 },
      interactive: false,
    });

    // Add the route as a line
    mapRef.current.on('load', () => {
      if (!mapRef.current?.getSource('route')) {
        mapRef.current?.addSource('route', {
          type: 'geojson',
          data: {
            type: 'Feature',
            properties: {},
            geometry: {
              type: 'LineString',
              coordinates: coordinates,
            },
          },
        });
        mapRef.current?.addLayer({
          id: 'route',
          type: 'line',
          source: 'route',
          layout: {
            'line-join': 'round',
            'line-cap': 'round',
          },
          paint: {
            'line-color': '#3b82f6',
            'line-width': 4,
          },
        });
      }
    });

    return () => {
      mapRef.current?.remove();
    };
  }, [summary_polyline]);

  return (
    <div
      ref={mapContainer}
      style={{
        width: '100%',
        height: `${height}px`,
        borderRadius: '0.5rem',
        overflow: 'hidden',
        marginTop: 8,
      }}
      className="shadow-card"
    />
  );
};

export default MapboxActivityMap;
