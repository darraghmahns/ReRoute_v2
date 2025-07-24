import React, { useState } from 'react';
import {
  getStravaAuthUrl,
  disconnectStrava,
  syncStravaActivities,
  refreshStravaActivities,
} from '../services/strava';
import { Button } from './ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import {
  Activity,
  Unlink,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Database,
} from 'lucide-react';

interface StravaConnectionProps {
  isConnected: boolean;
  athleteName?: string;
  onConnectionChange: (connected: boolean) => void;
}

const StravaConnection: React.FC<StravaConnectionProps> = ({
  isConnected,
  athleteName,
  onConnectionChange,
}) => {
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [messageType, setMessageType] = useState<'success' | 'error'>(
    'success'
  );

  const handleConnect = async () => {
    try {
      setLoading(true);
      setMessage(null);

      const { auth_url } = await getStravaAuthUrl();

      // Open Strava authorization in a new window
      const width = 500;
      const height = 600;
      const left = window.screenX + (window.outerWidth - width) / 2;
      const top = window.screenY + (window.outerHeight - height) / 2;

      const authWindow = window.open(
        auth_url,
        'strava-auth',
        `width=${width},height=${height},left=${left},top=${top}`
      );

      // Check if the window was opened successfully
      if (!authWindow) {
        setMessageType('error');
        setMessage('Please allow popups to connect to Strava.');
        return;
      }

      // Poll for window closure and check for callback
      const checkClosed = setInterval(() => {
        if (authWindow.closed) {
          clearInterval(checkClosed);
          // Refresh the page or update state to reflect connection
          window.location.reload();
        }
      }, 1000);
    } catch (error) {
      setMessageType('error');
      setMessage(
        error instanceof Error
          ? error.message
          : 'Failed to get Strava authorization URL.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setLoading(true);
      setMessage(null);

      await disconnectStrava();
      onConnectionChange(false);

      setMessageType('success');
      setMessage('Successfully disconnected from Strava.');

      // Clear message after 3 seconds
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessageType('error');
      setMessage(
        error instanceof Error
          ? error.message
          : 'Failed to disconnect from Strava.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      setMessage(null);

      const result = await syncStravaActivities();

      setMessageType('success');
      setMessage(
        `Successfully synced ${result.activities_count} activities from Strava!`
      );

      // Clear message after 5 seconds
      setTimeout(() => setMessage(null), 5000);
    } catch (error) {
      setMessageType('error');
      setMessage(
        error instanceof Error
          ? error.message
          : 'Failed to sync activities from Strava.'
      );
    } finally {
      setSyncing(false);
    }
  };

  const handleFullRefresh = async () => {
    try {
      setRefreshing(true);
      setMessage(null);

      const result = await refreshStravaActivities();

      setMessageType('success');
      setMessage(
        `Full refresh complete! Cleared ${result.deleted_count} old activities, added ${result.added_count} fresh activities.`
      );

      // Clear message after 8 seconds (longer for full refresh)
      setTimeout(() => setMessage(null), 8000);
    } catch (error) {
      setMessageType('error');
      setMessage(
        error instanceof Error
          ? error.message
          : 'Failed to refresh activities from Strava.'
      );
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Strava Connection
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">
              {isConnected ? 'Connected to Strava' : 'Not connected to Strava'}
            </p>
            {isConnected && athleteName && (
              <p className="text-sm text-gray-500">
                Connected as: {athleteName}
              </p>
            )}
          </div>
          <div
            className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`}
          />
        </div>

        {/* Message */}
        {message && (
          <div
            className={`flex items-center gap-2 p-3 rounded-md ${
              messageType === 'success'
                ? 'bg-green-50 text-green-800'
                : 'bg-red-50 text-red-800'
            }`}
          >
            {messageType === 'success' ? (
              <CheckCircle className="w-4 h-4" />
            ) : (
              <AlertCircle className="w-4 h-4" />
            )}
            <span className="text-sm">{message}</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-2">
          {!isConnected ? (
            <Button
              onClick={handleConnect}
              disabled={loading}
              className="flex items-center gap-2 p-0 bg-transparent hover:bg-transparent shadow-none border-none"
              style={{ minWidth: 0, minHeight: 0 }}
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <img
                  src="/src/assets/1.1 Connect with Strava Buttons/Connect with Strava Orange/btn_strava_connect_with_orange.svg"
                  alt="Connect with Strava"
                  style={{ height: '40px', width: 'auto', display: 'block' }}
                />
              )}
            </Button>
          ) : (
            <>
              <Button
                onClick={handleSync}
                disabled={syncing || refreshing}
                variant="outline"
                className="flex items-center gap-2"
              >
                {syncing ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                Sync Activities
              </Button>
              <Button
                onClick={handleFullRefresh}
                disabled={syncing || refreshing}
                variant="outline"
                className="flex items-center gap-2 bg-blue-50 text-blue-700 hover:bg-blue-100 border-blue-200"
              >
                {refreshing ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Database className="w-4 h-4" />
                )}
                Full Refresh
              </Button>
              <Button
                onClick={handleDisconnect}
                disabled={loading || syncing || refreshing}
                variant="outline"
                className="flex items-center gap-2 text-red-600 hover:text-red-700"
              >
                {loading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Unlink className="w-4 h-4" />
                )}
                Disconnect
              </Button>
            </>
          )}
        </div>

        {/* Info */}
        <div className="text-xs text-gray-500 space-y-1">
          {isConnected ? (
            <>
              <p>
                Connected to Strava. Your activities will be synced
                automatically.
              </p>
              <p>
                <strong>Sync Activities:</strong> Updates existing activities
                and adds new ones.
              </p>
              <p>
                <strong>Full Refresh:</strong> Clears all data and re-syncs
                everything. Use when AI analyzes old data or activities seem
                stale.
              </p>
            </>
          ) : (
            <p>
              Connect your Strava account to sync your cycling activities and
              get personalized insights.
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default StravaConnection;
