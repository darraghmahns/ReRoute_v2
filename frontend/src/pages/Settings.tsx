import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { getCurrentUserWithProfile } from '../services/auth';
import StravaConnection from '../components/StravaConnection';
import { ChangePasswordModal } from '../components/ChangePasswordModal';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { User, Shield, Palette } from 'lucide-react';
import type { Profile } from '../types';

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [stravaConnected, setStravaConnected] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const userData = await getCurrentUserWithProfile();
        setProfile(userData.profile);
        setStravaConnected(!!userData.profile?.strava_user_id);
      } catch (error) {
        console.error('Failed to fetch profile:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  if (loading) {
    return (
      <div className="min-h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-reroute-primary mx-auto mb-4"></div>
          <p className="text-white">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Settings</h1>
          <p className="text-gray-400 mt-2">
            Manage your account and preferences
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Strava Connection */}
          <div className="lg:col-span-2">
            <StravaConnection
              isConnected={stravaConnected}
              athleteName={
                profile?.strava_user_id ? 'Connected Athlete' : undefined
              }
              onConnectionChange={setStravaConnected}
            />
          </div>

          {/* Account Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="w-5 h-5" />
                Account Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-white mb-1">
                  Email
                </label>
                <p className="text-sm text-gray-300">{user?.email}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-1">
                  Full Name
                </label>
                <p className="text-sm text-gray-300">
                  {user?.full_name || 'Not set'}
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={() => navigate('/profile')}>
                Edit Profile
              </Button>
            </CardContent>
          </Card>

          {/* Privacy & Security */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Privacy & Security
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Change Password</p>
                  <p className="text-xs text-gray-400">Update your password</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowChangePassword(true)}
                >
                  Change
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Appearance */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="w-5 h-5" />
                Appearance
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Theme</p>
                  <p className="text-xs text-gray-400">
                    Choose your preferred theme
                  </p>
                </div>
                <span className="text-sm text-gray-300">Dark</span>
              </div>
            </CardContent>
          </Card>
        </div>

        <ChangePasswordModal
          isOpen={showChangePassword}
          onClose={() => setShowChangePassword(false)}
        />
      </div>
    </div>
  );
};

export default Settings;
