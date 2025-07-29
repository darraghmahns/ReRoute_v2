import axios from 'axios';
import type { Profile, StravaActivity } from '../types';

const API_URL = import.meta.env.VITE_API_URL || '';
const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    Authorization: `Bearer ${token}`,
  };
};

export const getProfile = async (): Promise<Profile> => {
  try {
    const response = await axios.get(`${API_URL}/api/profiles/me`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching profile:', error);
    throw error;
  }
};

export const updateProfile = async (
  profileData: Partial<Profile>
): Promise<Profile> => {
  try {
    const response = await axios.put(`${API_URL}/api/profiles/me`, profileData, {
      headers: getAuthHeaders(),
    });
    return response.data;
  } catch (error) {
    console.error('Error updating profile:', error);
    throw error;
  }
};

export const getStravaActivities = async (): Promise<StravaActivity[]> => {
  try {
    const response = await axios.get(`${API_URL}/api/strava/activities`, {
      headers: getAuthHeaders(),
    });
    return response.data.activities || [];
  } catch (error) {
    console.error('Error fetching Strava activities:', error);
    return [];
  }
};

export const getCachedActivities = async (): Promise<StravaActivity[]> => {
  try {
    const response = await axios.get(`${API_URL}/api/strava/activities/db`, {
      headers: getAuthHeaders(),
    });
    return response.data || [];
  } catch (error) {
    console.error('Error fetching cached activities:', error);
    return [];
  }
};

export const syncStravaActivities = async (): Promise<{
  message: string;
  activities_count: number;
}> => {
  try {
    const response = await axios.post(
      `${API_URL}/api/strava/sync`,
      {},
      {
        headers: getAuthHeaders(),
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error syncing Strava activities:', error);
    throw error;
  }
};

// Helper function to calculate statistics from activities
export const calculateStats = (activities: StravaActivity[]) => {
  if (!activities.length) {
    return {
      totalDistance: 0,
      totalTime: 0,
      totalActivities: 0,
      totalElevation: 0,
      averageSpeed: 0,
      maxDistance: 0,
      maxElevation: 0,
    };
  }

  const totalDistance = activities.reduce(
    (sum, activity) => sum + activity.distance_m,
    0
  );
  const totalTime = activities.reduce(
    (sum, activity) => sum + activity.moving_time_s,
    0
  );
  const totalElevation = activities.reduce(
    (sum, activity) => sum + activity.total_elevation_gain_m,
    0
  );
  const totalActivities = activities.length;

  const averageSpeed = (totalDistance / totalTime) * 20.237; // Convert m/s to mph
  const maxDistance = Math.max(...activities.map((a) => a.distance_m));
  const maxElevation = Math.max(
    ...activities.map((a) => a.total_elevation_gain_m)
  );

  return {
    totalDistance: totalDistance * 0.000621371, // Convert to miles
    totalTime: totalTime / 3600, // Convert to hours
    totalActivities,
    totalElevation: totalElevation * 30.2884, // Convert to feet
    averageSpeed,
    maxDistance: maxDistance * 0.000621371, // Convert to miles
    maxElevation: maxElevation * 30.2884, // Convert to feet
  };
};

// Helper function to get recent activities
export const getRecentActivities = (
  activities: StravaActivity[],
  limit: number = 5
) => {
  return activities
    .sort(
      (a, b) =>
        new Date(b.start_date).getTime() - new Date(a.start_date).getTime()
    )
    .slice(0, limit);
};

// Helper function to format distance for display (imperial)
export const formatDistance = (distanceMiles: number): string => {
  if (distanceMiles >= 1000) {
    return `${(distanceMiles / 1000).toFixed(1)}k mi`;
  }
  return `${distanceMiles.toFixed(1)} mi`;
};

// Helper function to format time for display
export const formatTime = (hours: number): string => {
  if (hours < 1) {
    const minutes = Math.round(hours * 60);
    return `${minutes}m`;
  }
  const wholeHours = Math.floor(hours);
  const minutes = Math.round((hours - wholeHours) * 60);
  return `${wholeHours}h ${minutes}m`;
};

// Helper function to format elevation for display (imperial)
export const formatElevation = (feet: number): string => {
  if (feet >= 1000) {
    return `${(feet / 1000).toFixed(1)}k ft`;
  }
  return `${Math.round(feet)} ft`;
};
