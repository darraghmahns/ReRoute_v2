import axios from 'axios';
import { getToken } from './auth';

const API_URL = import.meta.env.VITE_API_URL || '';

export interface RouteGenerationParams {
  start_lat: number;
  start_lng: number;
  end_lat?: number;
  end_lng?: number;
  profile: 'bike' | 'gravel' | 'mountain';
  route_type: 'road' | 'gravel' | 'mountain' | 'urban';
  distance_km?: number;
  is_loop: boolean;
  avoid_highways?: boolean;
  elevation_preference?: 'flat' | 'rolling' | 'hilly';
  waypoints?: Array<{
    lat: number;
    lng: number;
    name?: string;
    waypoint_type: 'start' | 'end' | 'via' | 'poi';
  }>;
  use_strava_segments?: boolean;
  strava_activity_type?: string;
}

export interface RouteCreate {
  name: string;
  description?: string;
  route_type: 'road' | 'gravel' | 'mountain' | 'urban';
  profile: 'bike' | 'gravel' | 'mountain';
  is_public?: boolean;
  generation_params: RouteGenerationParams;
}

export interface Route {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  route_type: 'road' | 'gravel' | 'mountain' | 'urban';
  profile: 'bike' | 'gravel' | 'mountain';
  geometry?: {
    type: 'LineString';
    coordinates: number[][];
  };
  waypoints?: Array<{
    lat: number;
    lng: number;
    name?: string;
  }>;
  elevation_profile?: Array<{
    distance: number;
    elevation: number;
  }>;
  distance_m: number;
  total_elevation_gain_m: number;
  total_elevation_loss_m: number;
  estimated_time_s?: number;
  difficulty_score?: number;
  start_lat: number;
  start_lng: number;
  end_lat: number;
  end_lng: number;
  is_loop: boolean;
  strava_segments?: Array<{
    id: string;
    name: string;
    distance_m: number;
    average_grade: number;
    popularity_score: number;
  }>;
  popularity_score?: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface RouteListItem {
  id: string;
  name: string;
  route_type: 'road' | 'gravel' | 'mountain' | 'urban';
  distance_m: number;
  total_elevation_gain_m: number;
  difficulty_score?: number;
  is_loop: boolean;
  is_public: boolean;
  created_at: string;
}

export interface RouteGenerationResponse {
  message: string;
  route: Route;
  generation_time_ms: number;
}

const getAuthHeaders = () => {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const generateRoute = async (
  params: RouteGenerationParams
): Promise<RouteGenerationResponse> => {
  try {
    const response = await axios.post(`${API_URL}/api/routes/generate`, params, {
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        throw new Error('Unauthorized. Please log in again.');
      } else if (error.response?.status === 400) {
        throw new Error(
          error.response.data?.detail || 'Invalid route parameters.'
        );
      } else if (error.response?.status === 500) {
        throw new Error('Route generation failed. Please try again.');
      }
    }
    throw new Error('An unexpected error occurred during route generation.');
  }
};

export const generateLoopRoute = async (
  lat: number,
  lng: number,
  distance_km: number,
  profile: 'bike' | 'gravel' | 'mountain' = 'bike',
  route_type: 'road' | 'gravel' | 'mountain' | 'urban' = 'road'
): Promise<RouteGenerationResponse> => {
  try {
    const response = await axios.post(`${API_URL}/api/routes/loops`, null, {
      params: {
        lat,
        lng,
        distance_km,
        profile,
        route_type,
      },
      headers: getAuthHeaders(),
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        throw new Error('Unauthorized. Please log in again.');
      } else if (error.response?.status === 400) {
        throw new Error(
          error.response.data?.detail || 'Invalid parameters for loop route.'
        );
      } else if (error.response?.status === 500) {
        throw new Error('Loop route generation failed. Please try again.');
      }
    }
    throw new Error(
      'An unexpected error occurred during loop route generation.'
    );
  }
};

export const generateAILoopRoute = async (
  start_lat: number,
  start_lng: number,
  distance_km: number,
  profile: 'bike' | 'gravel' | 'mountain' = 'bike',
  route_type: 'road' | 'gravel' | 'mountain' | 'urban' = 'road',
  num_waypoints: number = 4
): Promise<RouteGenerationResponse> => {
  try {
    const response = await axios.post(
      `${API_URL}/api/routes/generate-ai-loop`,
      null,
      {
        params: {
          start_lat,
          start_lng,
          distance_km,
          profile,
          route_type,
          num_waypoints,
        },
        headers: getAuthHeaders(),
      }
    );
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        throw new Error('Unauthorized. Please log in again.');
      } else if (error.response?.status === 400) {
        throw new Error(
          error.response.data?.detail || 'Invalid parameters for AI loop route.'
        );
      } else if (error.response?.status === 500) {
        throw new Error('AI loop route generation failed. Please try again.');
      }
    }
    throw new Error(
      'An unexpected error occurred during AI loop route generation.'
    );
  }
};

export const getUserRoutes = async (
  skip: number = 0,
  limit: number = 20,
  route_type?: string
): Promise<RouteListItem[]> => {
  try {
    const params: Record<string, string | number> = { skip, limit };
    if (route_type && route_type !== 'all') {
      params.route_type = route_type;
    }

    const response = await axios.get(`${API_URL}/api/routes/`, {
      params,
      headers: getAuthHeaders(),
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        throw new Error('Unauthorized. Please log in again.');
      }
    }
    throw new Error('Failed to fetch routes.');
  }
};

export const getRoute = async (routeId: string): Promise<Route> => {
  try {
    const response = await axios.get(`${API_URL}/api/routes/${routeId}`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        throw new Error('Unauthorized. Please log in again.');
      } else if (error.response?.status === 404) {
        throw new Error('Route not found.');
      }
    }
    throw new Error('Failed to fetch route.');
  }
};

export const updateRoute = async (
  routeId: string,
  updates: { name?: string; description?: string; is_public?: boolean }
): Promise<Route> => {
  try {
    const response = await axios.put(`${API_URL}/api/routes/${routeId}`, updates, {
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        throw new Error('Unauthorized. Please log in again.');
      } else if (error.response?.status === 404) {
        throw new Error('Route not found.');
      }
    }
    throw new Error('Failed to update route.');
  }
};

export const deleteRoute = async (routeId: string): Promise<void> => {
  try {
    await axios.delete(`${API_URL}/api/routes/${routeId}`, {
      headers: getAuthHeaders(),
    });
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        throw new Error('Unauthorized. Please log in again.');
      } else if (error.response?.status === 404) {
        throw new Error('Route not found.');
      }
    }
    throw new Error('Failed to delete route.');
  }
};

export const downloadGPX = async (routeId: string): Promise<void> => {
  try {
    const response = await axios.get(`${API_URL}/api/routes/${routeId}/gpx`, {
      headers: getAuthHeaders(),
      responseType: 'blob',
    });

    // Create download link
    const blob = new Blob([response.data], { type: 'application/gpx+xml' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `route_${routeId}.gpx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        throw new Error('Unauthorized. Please log in again.');
      } else if (error.response?.status === 404) {
        throw new Error('Route not found.');
      }
    }
    throw new Error('Failed to download GPX file.');
  }
};

export const getRouteSuggestions = async (
  routeId: string
): Promise<unknown> => {
  try {
    const response = await axios.get(
      `${API_URL}/api/routes/${routeId}/suggestions`,
      {
        headers: getAuthHeaders(),
      }
    );
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        throw new Error('Unauthorized. Please log in again.');
      } else if (error.response?.status === 404) {
        throw new Error('Route not found.');
      }
    }
    throw new Error('Failed to fetch route suggestions.');
  }
};
