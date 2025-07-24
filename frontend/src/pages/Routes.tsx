import React, { useState, useEffect } from 'react';
import {
  MapPin,
  Bike,
  Mountain,
  Map as MapIcon,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import RouteMap from '../components/RouteMap';
import {
  generateAILoopRoute,
  getUserRoutes,
  deleteRoute,
  downloadGPX,
  getRoute,
  type RouteListItem,
  type Route,
} from '../services/routes';
import { useAuth } from '../hooks/useAuth';

interface RouteFormData {
  name: string;
  distance: string;
  startLocation: { lat: number; lng: number } | null;
  endLocation: { lat: number; lng: number } | null;
  profile: 'bike' | 'gravel' | 'mountain';
  routeType: 'road' | 'gravel' | 'mountain' | 'urban';
  isLoop: boolean;
  useStravaSegments: boolean;
  useAIGeneration: boolean;
}

interface GeneratedRoute {
  id: string;
  name: string;
  distance_m: number;
  geometry?: {
    type: 'LineString';
    coordinates: number[][];
  };
}

const bikeTypes = [
  { id: 'bike', label: 'Road Bike', icon: Bike },
  { id: 'gravel', label: 'Gravel', icon: MapIcon },
  { id: 'mountain', label: 'Mountain', icon: Mountain },
];

const Routes: React.FC = () => {
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');

  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedBike, setSelectedBike] = useState<string>('bike');

  // Route generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [formData, setFormData] = useState<RouteFormData>({
    name: '',
    distance: '',
    startLocation: null,
    endLocation: null,
    profile: 'bike',
    routeType: 'road',
    isLoop: true,
    useStravaSegments: false,
    useAIGeneration: true,
  });

  // User routes state
  const [userRoutes, setUserRoutes] = useState<RouteListItem[]>([]);
  const [isLoadingRoutes, setIsLoadingRoutes] = useState(false);
  const [routesError, setRoutesError] = useState<string | null>(null);

  // Generated route preview
  const [previewRoute, setPreviewRoute] = useState<GeneratedRoute | null>(null);

  // Route expansion state
  const [expandedRoutes, setExpandedRoutes] = useState<Set<string>>(new Set());
  const [routeDetails, setRouteDetails] = useState<Map<string, Route>>(
    new Map()
  );
  const [loadingRouteDetails, setLoadingRouteDetails] = useState<Set<string>>(
    new Set()
  );

  // Load user routes on component mount
  useEffect(() => {
    if (user) {
      loadUserRoutes();
    }
  }, [user]);

  const loadUserRoutes = async () => {
    if (!user) return;

    setIsLoadingRoutes(true);
    setRoutesError(null);

    try {
      const routes = await getUserRoutes(
        0,
        50,
        selectedType !== 'all' ? selectedType : undefined
      );
      setUserRoutes(routes);
    } catch (error) {
      setRoutesError(
        error instanceof Error ? error.message : 'Failed to load routes'
      );
    } finally {
      setIsLoadingRoutes(false);
    }
  };

  // Filter and sort routes based on search and type
  const filteredRoutes = userRoutes
    .filter((route) => {
      const matchesSearch = route.name
        .toLowerCase()
        .includes(searchTerm.toLowerCase());
      const matchesType =
        selectedType === 'all' || route.route_type === selectedType;
      return matchesSearch && matchesType;
    })
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

  const handleLocationSelect = (lat: number, lng: number) => {
    setFormData((prev) => ({
      ...prev,
      startLocation: { lat, lng },
    }));
  };

  const handleGenerateRoute = async () => {
    if (
      !formData.startLocation ||
      !formData.name.trim() ||
      !formData.distance.trim()
    ) {
      setGenerationError(
        'Please provide a route name, distance, and select a start location'
      );
      return;
    }

    const distance = parseFloat(formData.distance);
    if (isNaN(distance) || distance <= 0) {
      setGenerationError('Please enter a valid distance greater than 0');
      return;
    }

    setIsGenerating(true);
    setGenerationError(null);

    try {
      // Always use AI loop generation
      const distanceKm = distance * 1.609344; // Convert miles to kilometers
      const result = await generateAILoopRoute(
        formData.startLocation.lat,
        formData.startLocation.lng,
        distanceKm,
        formData.profile,
        formData.routeType,
        4 // Default 4 waypoints
      );

      setPreviewRoute({
        id: result.route.id,
        name: result.route.name,
        distance_m: result.route.distance_m,
        geometry: result.route.geometry,
      });
      await loadUserRoutes();

      // Reset form after successful generation
      setFormData({
        name: '',
        distance: '',
        startLocation: null,
        endLocation: null,
        profile: 'bike',
        routeType: 'road',
        isLoop: true,
        useStravaSegments: false,
        useAIGeneration: true,
      });
      setSelectedBike('bike');
    } catch (error) {
      setGenerationError(
        error instanceof Error ? error.message : 'Failed to generate route'
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDeleteRoute = async (routeId: string) => {
    if (!confirm('Are you sure you want to delete this route?')) return;

    try {
      await deleteRoute(routeId);
      await loadUserRoutes();
    } catch (error) {
      console.error('Failed to delete route:', error);
    }
  };

  const handleDownloadGPX = async (routeId: string) => {
    try {
      await downloadGPX(routeId);
    } catch (error) {
      console.error('Failed to download GPX:', error);
    }
  };

  const toggleRouteExpansion = async (routeId: string) => {
    const newExpanded = new Set(expandedRoutes);

    if (expandedRoutes.has(routeId)) {
      // Collapse
      newExpanded.delete(routeId);
    } else {
      // Expand - load route details if not already loaded
      newExpanded.add(routeId);

      if (!routeDetails.has(routeId)) {
        setLoadingRouteDetails((prev) => new Set(prev).add(routeId));
        try {
          const route = await getRoute(routeId);
          setRouteDetails((prev) => new Map(prev).set(routeId, route));
        } catch (error) {
          console.error('Failed to load route details:', error);
          newExpanded.delete(routeId); // Don't expand if failed to load
        } finally {
          setLoadingRouteDetails((prev) => {
            const newSet = new Set(prev);
            newSet.delete(routeId);
            return newSet;
          });
        }
      }
    }

    setExpandedRoutes(newExpanded);
  };

  const formatDistance = (meters: number) => {
    const miles = meters * 0.000621371;
    return `${miles.toFixed(1)} mi`;
  };

  const formatElevation = (meters: number) => {
    const feet = meters * 3.28084;
    return `${Math.round(feet)} ft`;
  };

  const getDifficultyLevel = (score?: number) => {
    if (!score) return 'Easy';
    if (score < 3) return 'Easy';
    if (score < 5) return 'Moderate';
    if (score < 7) return 'Hard';
    return 'Expert';
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Easy':
        return 'bg-green-500';
      case 'Moderate':
        return 'bg-yellow-500';
      case 'Hard':
        return 'bg-orange-500';
      case 'Expert':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'road':
        return 'bg-reroute-primary/20 text-reroute-primary';
      case 'gravel':
        return 'bg-reroute-yellow/20 text-reroute-yellow';
      case 'mountain':
        return 'bg-reroute-purple/20 text-reroute-purple';
      case 'urban':
        return 'bg-reroute-card text-gray-400';
      default:
        return 'bg-reroute-card text-gray-400';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-reroute-bg-900 to-reroute-bg-700 py-8 px-2">
      <div className="max-w-5xl mx-auto space-y-10">
        {/* Route Planner Card */}
        <Card className="bg-reroute-card rounded-2xl shadow-card p-8">
          <CardHeader className="pb-4">
            <CardTitle className="text-2xl font-bold text-white mb-1">
              Montana Route Planner
            </CardTitle>
            <p className="text-gray-400 text-base">
              Generate cycling routes using custom GraphHopper routing optimized
              for Montana
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <label className="block text-gray-300 text-sm mb-1">
                  Route Name
                </label>
                <Input
                  className="bg-[#16213a] text-white placeholder-gray-500 border-none"
                  placeholder="e.g., Helena to Bozeman Challenge"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, name: e.target.value }))
                  }
                />
              </div>
              <div className="flex-1">
                <label className="block text-gray-300 text-sm mb-1">
                  Distance (mi) *
                </label>
                <Input
                  className="bg-[#16213a] text-white placeholder-gray-500 border-none"
                  placeholder="e.g., 40"
                  type="number"
                  min="1"
                  step="0.1"
                  required
                  value={formData.distance}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      distance: e.target.value,
                    }))
                  }
                />
              </div>
            </div>
            <div>
              <label className="block text-gray-300 text-sm mb-1">
                Start Location (Montana)
              </label>
              <p className="text-xs text-gray-500 mb-2">
                Click on the map to set starting location
              </p>
              <div className="rounded-lg overflow-hidden border border-reroute-card mb-2">
                <RouteMap
                  onLocationSelect={handleLocationSelect}
                  selectedLocation={formData.startLocation}
                  routeGeometry={previewRoute?.geometry}
                  height="14rem"
                />
              </div>
              {formData.startLocation && (
                <p className="text-xs text-green-400 mb-2">
                  Selected: {formData.startLocation.lat.toFixed(4)},{' '}
                  {formData.startLocation.lng.toFixed(4)}
                </p>
              )}
              {previewRoute && (
                <div className="flex items-center justify-between bg-green-500/10 border border-green-500/20 rounded-lg p-3 mb-2">
                  <p className="text-xs text-green-400">
                    Preview: {previewRoute.name} (
                    {formatDistance(previewRoute.distance_m)})
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-green-500/50 text-green-400 hover:bg-green-500/10 text-xs px-2 py-1"
                    onClick={() => setPreviewRoute(null)}
                  >
                    Clear
                  </Button>
                </div>
              )}
              <Button
                className="mt-2 bg-reroute-gray text-reroute-card font-semibold"
                onClick={() => {
                  if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition((position) => {
                      setFormData((prev) => ({
                        ...prev,
                        startLocation: {
                          lat: position.coords.latitude,
                          lng: position.coords.longitude,
                        },
                      }));
                    });
                  }
                }}
              >
                Use My Location
              </Button>
            </div>
            <div>
              <label className="block text-gray-300 text-sm mb-2">
                Bike Type
              </label>
              <div className="flex gap-2 mb-2">
                {bikeTypes.map((type) => (
                  <button
                    key={type.id}
                    onClick={() => {
                      setSelectedBike(type.id);
                      setFormData((prev) => ({
                        ...prev,
                        profile: type.id as 'bike' | 'gravel' | 'mountain',
                        routeType:
                          type.id === 'bike'
                            ? 'road'
                            : (type.id as 'road' | 'gravel' | 'mountain'),
                      }));
                    }}
                    type="button"
                    className={`flex items-center gap-2 px-4 py-2 rounded-full font-medium text-sm transition-colors border-2
                      ${
                        selectedBike === type.id
                          ? 'bg-reroute-tab-active text-reroute-card border-reroute-tab-active shadow'
                          : 'bg-[#16213a] text-white/80 border-transparent hover:bg-white/10'
                      }
                    `}
                  >
                    <type.icon className="w-5 h-5" />
                    {type.label}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-4 mb-2">
                <label className="flex items-center gap-2 text-sm text-gray-300">
                  <input
                    type="checkbox"
                    checked={formData.useStravaSegments}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        useStravaSegments: e.target.checked,
                      }))
                    }
                    className="rounded"
                  />
                  Use popular Strava segments
                </label>
              </div>
              <div className="text-xs text-gray-400 space-y-1">
                <div>
                  <span className="font-bold text-white">Road Bike:</span>{' '}
                  Optimized for paved roads and cycleways
                </div>
                <div>
                  <span className="font-bold text-white">Gravel:</span>{' '}
                  Prioritizes gravel roads, dirt tracks, and unpaved surfaces
                </div>
                <div>
                  <span className="font-bold text-white">Mountain:</span>{' '}
                  Optimized for trails, paths, and technical terrain
                </div>
                <div>
                  <span className="font-bold text-white">
                    AI Loop Generation:
                  </span>{' '}
                  Automatically creates optimal loop routes with waypoints
                  snapped to roads
                </div>
              </div>
            </div>
            {generationError && (
              <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                <AlertCircle className="w-4 h-4 text-red-400" />
                <span className="text-red-400 text-sm">{generationError}</span>
              </div>
            )}
            <div className="flex gap-2 mt-4">
              <Button
                className="flex-1 bg-reroute-primary text-white font-semibold"
                onClick={handleGenerateRoute}
                disabled={
                  isGenerating ||
                  !formData.name.trim() ||
                  !formData.startLocation ||
                  !formData.distance.trim()
                }
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  'Generate Route'
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Your Routes Card */}
        <Card className="bg-reroute-card rounded-2xl shadow-card p-8">
          <CardHeader className="pb-4">
            <CardTitle className="text-2xl font-bold text-white mb-1">
              Your Routes
            </CardTitle>
            <p className="text-gray-400 text-base">
              {isLoadingRoutes
                ? 'Loading...'
                : `${filteredRoutes.length} routes`}
            </p>
          </CardHeader>

          {/* Search and Filter Controls */}
          <div className="mb-6 flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Input
                className="bg-[#16213a] text-white placeholder-gray-500 border-none"
                placeholder="Search routes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="bg-[#16213a] text-white border-none rounded-lg px-3 py-2"
              >
                <option value="all">All Types</option>
                <option value="road">Road</option>
                <option value="gravel">Gravel</option>
                <option value="mountain">Mountain</option>
                <option value="urban">Urban</option>
              </select>
              <Button
                variant="outline"
                size="sm"
                className="border-reroute-gray text-white hover:bg-reroute-card"
                onClick={loadUserRoutes}
              >
                Refresh
              </Button>
            </div>
          </div>

          <CardContent className="space-y-6">
            {routesError && (
              <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                <AlertCircle className="w-4 h-4 text-red-400" />
                <span className="text-red-400 text-sm">{routesError}</span>
              </div>
            )}

            {isLoadingRoutes ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-white" />
                <span className="ml-2 text-white">Loading routes...</span>
              </div>
            ) : (
              <>
                {filteredRoutes.map((route) => {
                  const difficulty = getDifficultyLevel(route.difficulty_score);
                  const difficultyColor = getDifficultyColor(difficulty);
                  const isExpanded = expandedRoutes.has(route.id);
                  const isLoadingDetails = loadingRouteDetails.has(route.id);
                  const routeDetail = routeDetails.get(route.id);

                  return (
                    <div
                      key={route.id}
                      className="mb-6 rounded-xl bg-[#16213a] shadow-card overflow-hidden"
                    >
                      {/* Route Header - Clickable */}
                      <div
                        className="p-6 cursor-pointer hover:bg-[#1a2441] transition-colors"
                        onClick={() => toggleRouteExpansion(route.id)}
                      >
                        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-lg font-bold text-white">
                                {route.name}
                              </span>
                              <span
                                className={`px-2 py-1 rounded-full text-xs font-bold ${difficultyColor} text-white uppercase`}
                              >
                                {difficulty}
                              </span>
                              <span
                                className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(route.route_type)}`}
                              >
                                {route.route_type}
                              </span>
                              {isExpanded ? (
                                <ChevronUp className="w-4 h-4 text-gray-400" />
                              ) : (
                                <ChevronDown className="w-4 h-4 text-gray-400" />
                              )}
                            </div>
                            <div className="flex flex-wrap gap-4 text-sm text-gray-400 mb-2">
                              <span className="flex items-center gap-1">
                                <MapPin className="w-4 h-4" />
                                {formatDistance(route.distance_m)}
                              </span>
                              <span className="flex items-center gap-1">
                                <Mountain className="w-4 h-4 text-green-400" />
                                {formatElevation(
                                  route.total_elevation_gain_m
                                )}{' '}
                                gain
                              </span>
                              {route.total_elevation_gain_m > 0 && (
                                <span className="flex items-center gap-1">
                                  <Mountain className="w-4 h-4 text-red-400 rotate-180" />
                                  {formatElevation(
                                    route.total_elevation_gain_m
                                  )}{' '}
                                  loss
                                </span>
                              )}
                              <span className="flex items-center gap-1">
                                <MapIcon className="w-4 h-4" />
                                {route.is_loop ? 'Loop' : 'Point-to-Point'}
                              </span>
                            </div>
                            <p className="text-xs text-gray-500">
                              Created:{' '}
                              {new Date(route.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <div
                            className="flex gap-2"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Button
                              variant="outline"
                              size="sm"
                              className="border-reroute-gray text-white hover:bg-reroute-card"
                              onClick={() => handleDownloadGPX(route.id)}
                            >
                              Export GPX
                            </Button>
                            <Button
                              size="sm"
                              className="bg-red-500 hover:bg-red-600 text-white"
                              onClick={() => handleDeleteRoute(route.id)}
                            >
                              Delete
                            </Button>
                          </div>
                        </div>
                      </div>

                      {/* Collapsible Route Details */}
                      {isExpanded && (
                        <div className="border-t border-gray-600">
                          {isLoadingDetails ? (
                            <div className="p-6 flex items-center justify-center">
                              <Loader2 className="w-6 h-6 animate-spin text-white mr-2" />
                              <span className="text-white">
                                Loading route details...
                              </span>
                            </div>
                          ) : routeDetail ? (
                            <div className="p-6 space-y-4">
                              {/* Route Map */}
                              <div className="rounded-lg overflow-hidden border border-reroute-card">
                                <RouteMap
                                  onLocationSelect={() => {}} // No location selection in detail view
                                  selectedLocation={null}
                                  routeGeometry={routeDetail.geometry}
                                  height="20rem"
                                  interactive={true}
                                />
                              </div>

                              {/* Elevation Summary */}
                              {(routeDetail.total_elevation_gain_m > 0 ||
                                routeDetail.total_elevation_loss_m > 0) && (
                                <div className="bg-[#1a2441] rounded-lg p-4">
                                  <h4 className="font-semibold text-white mb-3">
                                    Elevation Profile
                                  </h4>
                                  <div className="grid grid-cols-3 gap-4 text-center">
                                    <div>
                                      <div className="text-green-400 text-xl font-bold">
                                        ⛰️
                                      </div>
                                      <div className="text-sm text-gray-400">
                                        Total Gain
                                      </div>
                                      <div className="text-white font-semibold">
                                        {formatElevation(
                                          routeDetail.total_elevation_gain_m
                                        )}
                                      </div>
                                    </div>
                                    <div>
                                      <div className="text-red-400 text-xl font-bold">
                                        ⬇️
                                      </div>
                                      <div className="text-sm text-gray-400">
                                        Total Loss
                                      </div>
                                      <div className="text-white font-semibold">
                                        {formatElevation(
                                          routeDetail.total_elevation_loss_m
                                        )}
                                      </div>
                                    </div>
                                    <div>
                                      <div className="text-blue-400 text-xl font-bold">
                                        📊
                                      </div>
                                      <div className="text-sm text-gray-400">
                                        Net Gain
                                      </div>
                                      <div className="text-white font-semibold">
                                        {formatElevation(
                                          routeDetail.total_elevation_gain_m -
                                            routeDetail.total_elevation_loss_m
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              )}

                              {/* Additional Route Details */}
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                <div className="space-y-2">
                                  <h4 className="font-semibold text-white">
                                    Route Details
                                  </h4>
                                  <div className="text-gray-400 space-y-1">
                                    <p>
                                      <span className="text-white">
                                        Distance:
                                      </span>{' '}
                                      {formatDistance(routeDetail.distance_m)}
                                    </p>
                                    <p>
                                      <span className="text-white">
                                        Elevation Gain:
                                      </span>{' '}
                                      {formatElevation(
                                        routeDetail.total_elevation_gain_m
                                      )}
                                    </p>
                                    <p>
                                      <span className="text-white">
                                        Elevation Loss:
                                      </span>{' '}
                                      {formatElevation(
                                        routeDetail.total_elevation_loss_m
                                      )}
                                    </p>
                                    {routeDetail.estimated_time_s && (
                                      <p>
                                        <span className="text-white">
                                          Estimated Time:
                                        </span>{' '}
                                        {Math.round(
                                          (routeDetail.estimated_time_s /
                                            3600) *
                                            10
                                        ) / 10}
                                        h
                                      </p>
                                    )}
                                  </div>
                                </div>

                                <div className="space-y-2">
                                  <h4 className="font-semibold text-white">
                                    Configuration
                                  </h4>
                                  <div className="text-gray-400 space-y-1">
                                    <p>
                                      <span className="text-white">
                                        Profile:
                                      </span>{' '}
                                      {routeDetail.profile}
                                    </p>
                                    <p>
                                      <span className="text-white">Type:</span>{' '}
                                      {routeDetail.route_type}
                                    </p>
                                    <p>
                                      <span className="text-white">Loop:</span>{' '}
                                      {routeDetail.is_loop ? 'Yes' : 'No'}
                                    </p>
                                    {routeDetail.popularity_score && (
                                      <p>
                                        <span className="text-white">
                                          Popularity:
                                        </span>{' '}
                                        {(
                                          routeDetail.popularity_score * 100
                                        ).toFixed(0)}
                                        %
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>

                              {routeDetail.description && (
                                <div>
                                  <h4 className="font-semibold text-white mb-2">
                                    Description
                                  </h4>
                                  <p className="text-gray-400 text-sm">
                                    {routeDetail.description}
                                  </p>
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="p-6 text-center text-gray-400">
                              Failed to load route details
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
                {filteredRoutes.length === 0 && !isLoadingRoutes && (
                  <div className="text-center py-12">
                    <p className="text-gray-400">
                      {userRoutes.length === 0
                        ? 'No routes generated yet. Create your first route above!'
                        : 'No routes found matching your criteria.'}
                    </p>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Routes;
