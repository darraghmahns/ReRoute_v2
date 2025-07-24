import { useState, useEffect } from 'react';
import { getStravaActivities, syncStravaActivities } from '../services/strava';
import type { StravaActivity } from '../types';

interface UseStravaReturn {
  activities: StravaActivity[];
  loading: boolean;
  error: string | null;
  syncActivities: () => Promise<void>;
  refreshActivities: () => Promise<void>;
}

export const useStrava = (): UseStravaReturn => {
  const [activities, setActivities] = useState<StravaActivity[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchActivities = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getStravaActivities();
      setActivities(response.activities);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to fetch activities'
      );
    } finally {
      setLoading(false);
    }
  };

  const syncActivities = async () => {
    try {
      setLoading(true);
      setError(null);
      await syncStravaActivities();
      // Refresh activities after sync
      await fetchActivities();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to sync activities'
      );
    } finally {
      setLoading(false);
    }
  };

  const refreshActivities = async () => {
    await fetchActivities();
  };

  // Load activities on mount
  useEffect(() => {
    fetchActivities();
  }, []);

  return {
    activities,
    loading,
    error,
    syncActivities,
    refreshActivities,
  };
};
