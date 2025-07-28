import axios from 'axios';
import type { StravaActivity, StravaZone } from '../types';

const API_URL = import.meta.env.VITE_API_URL || '';

// Get auth token for API requests
const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export interface StravaAuthResponse {
  message: string;
  athlete: {
    id: number;
    firstname: string;
    lastname: string;
    username: string;
  };
}

export interface StravaSyncResponse {
  message: string;
  activities_count: number;
  activities: Record<string, unknown>[];
}

export interface StravaRefreshResponse {
  message: string;
  deleted_count: number;
  added_count: number;
  sample_activities: Record<string, unknown>[];
}

export interface StravaActivitiesResponse {
  activities: StravaActivity[];
  count: number;
}

export interface StravaZonesResponse {
  zones: StravaZone[];
}

// Get Strava OAuth URL
export const getStravaAuthUrl = async (): Promise<{ auth_url: string }> => {
  const res = await axios.get(`${API_URL}/strava/auth-url`, {
    headers: getAuthHeaders(),
  });
  return res.data;
};

// Handle Strava OAuth callback
export const handleStravaCallback = async (
  code: string
): Promise<StravaAuthResponse> => {
  const res = await axios.post(
    `${API_URL}/strava/callback`,
    { code },
    {
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    }
  );
  return res.data;
};

// Sync activities from Strava
export const syncStravaActivities = async (): Promise<StravaSyncResponse> => {
  const res = await axios.post(
    `${API_URL}/strava/sync`,
    {},
    {
      headers: getAuthHeaders(),
    }
  );
  return res.data;
};

// Full refresh: Clear all activities and re-sync from Strava
export const refreshStravaActivities =
  async (): Promise<StravaRefreshResponse> => {
    const res = await axios.post(
      `${API_URL}/strava/sync/refresh`,
      {},
      {
        headers: getAuthHeaders(),
      }
    );
    return res.data;
  };

// Get activities from Strava
export const getStravaActivities =
  async (): Promise<StravaActivitiesResponse> => {
    const res = await axios.get(`${API_URL}/strava/activities`, {
      headers: getAuthHeaders(),
    });
    return res.data;
  };

// Get athlete zones from Strava
export const getStravaZones = async (): Promise<StravaZonesResponse> => {
  const res = await axios.post(
    `${API_URL}/strava/zones`,
    {},
    {
      headers: getAuthHeaders(),
    }
  );
  return res.data;
};

// Disconnect Strava
export const disconnectStrava = async (): Promise<{ message: string }> => {
  const res = await axios.delete(`${API_URL}/strava/disconnect`, {
    headers: getAuthHeaders(),
  });
  return res.data;
};
