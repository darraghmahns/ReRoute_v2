import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import SubscriptionSection from './Subscription';
import SettingsSection from './Settings';
import {
  User as UserIcon,
  Calendar,
  MapPin,
  Clock,
  TrendingUp,
  Edit,
  Camera,
  Activity,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import {
  getProfile,
  getStravaActivities,
  calculateStats,
  getRecentActivities,
  formatDistance,
  formatTime,
  formatElevation,
} from '../services/profile';
import type { Profile, StravaActivity, User } from '../types';
import Modal from '../components/ui/Modal';
import EditProfileForm from '../components/EditProfileForm';
import { getCurrentUser } from '../services/auth';

interface Stat {
  label: string;
  value: string;
  change?: string;
  icon: React.ReactNode;
  color: string;
}

const Profile: React.FC = () => {
  const [sidebarSection, setSidebarSection] = useState<
    'profile' | 'subscription' | 'settings'
  >('profile');
  const [activeTab, setActiveTab] = useState<'overview' | 'stats'>('overview');
  const [profile, setProfile] = useState<Profile | null>(null);
  const [activities, setActivities] = useState<StravaActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const [editOpen, setEditOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [profileData, activitiesData, userData] = await Promise.all([
          getProfile(),
          getStravaActivities(),
          getCurrentUser(),
        ]);
        setProfile(profileData);
        setActivities(activitiesData);
        setUser(userData);
      } catch (err) {
        console.error('Error fetching profile data:', err);
        setError('Failed to load profile data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const stats = calculateStats(activities);
  const recentActivities = getRecentActivities(activities, 3);

  const displayStats: Stat[] = [
    {
      label: 'Total Distance',
      value: formatDistance(stats.totalDistance),
      change: '+15% this month',
      icon: <MapPin className="w-6 h-6 text-white" />,
      color: 'bg-reroute-primary',
    },
    {
      label: 'Total Time',
      value: formatTime(stats.totalTime),
      change: '+8% this month',
      icon: <Clock className="w-6 h-6 text-white" />,
      color: 'bg-reroute-green',
    },
    {
      label: 'Activities',
      value: stats.totalActivities.toString(),
      change: '+12 this month',
      icon: <Calendar className="w-6 h-6 text-white" />,
      color: 'bg-reroute-purple',
    },
    {
      label: 'Total Elevation',
      value: formatElevation(stats.totalElevation),
      change: '+320 this month',
      icon: <TrendingUp className="w-6 h-6 text-white" />,
      color: 'bg-reroute-yellow',
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-white">Loading profile...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-400">{error}</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col md:flex-row">
      {/* Mobile Navigation */}
      <div className="md:hidden mb-4">
        <div className="flex gap-2 px-2 py-2 rounded-xl bg-reroute-tabbar shadow-lg overflow-x-auto">
          {[
            { id: 'profile', label: 'Profile' },
            { id: 'subscription', label: 'Subscription' },
            { id: 'settings', label: 'Settings' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() =>
                setSidebarSection(
                  item.id as 'profile' | 'subscription' | 'settings'
                )
              }
              className={`px-4 py-2 rounded-lg font-medium transition-colors text-sm whitespace-nowrap ${
                sidebarSection === item.id
                  ? 'bg-reroute-tab-active text-white shadow'
                  : 'bg-transparent text-white/80 hover:bg-white/10'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Desktop Sidebar */}
      <aside className="w-56 bg-reroute-card border-r border-reroute-card py-8 hidden md:block">
        <nav className="space-y-2 px-4">
          {[
            { id: 'profile', label: 'Profile' },
            { id: 'subscription', label: 'Subscription' },
            { id: 'settings', label: 'Settings' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() =>
                setSidebarSection(
                  item.id as 'profile' | 'subscription' | 'settings'
                )
              }
              className={`w-full text-left px-3 py-2 rounded transition-colors ${
                sidebarSection === item.id
                  ? 'bg-reroute-primary text-white'
                  : 'text-gray-400 hover:text-white hover:bg-reroute-card/80'
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <div className="flex-1 px-2 sm:px-4 lg:px-8 py-4 sm:py-8">
        {/* Back button */}
        <button
          onClick={() => navigate('/')}
          className="mb-4 text-sm text-reroute-primary hover:underline"
        >
          ← Back to Main
        </button>

        {/* Header */}
        <div className="mb-4 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-white capitalize">
            {sidebarSection}
          </h1>
        </div>

        {sidebarSection === 'profile' && (
          <>
            {/* Profile Header */}
            <Card className="mb-4 sm:mb-8 bg-reroute-card border-reroute-card">
              <CardContent className="p-3 sm:p-6">
                <div className="flex flex-col sm:flex-row items-center sm:items-start space-y-4 sm:space-y-0 sm:space-x-6">
                  <div className="relative flex-shrink-0">
                    <div className="w-20 h-20 sm:w-24 sm:h-24 bg-gradient-to-br from-reroute-primary to-reroute-purple rounded-full flex items-center justify-center">
                      <UserIcon className="w-10 h-10 sm:w-12 sm:h-12 text-white" />
                    </div>
                    <button className="absolute -bottom-1 -right-1 p-1.5 sm:p-2 bg-reroute-card rounded-full shadow-card hover:shadow-lg transition-shadow border border-reroute-gray">
                      <Camera className="w-3 h-3 sm:w-4 sm:h-4 text-gray-400" />
                    </button>
                  </div>
                  <div className="flex-1 text-center sm:text-left">
                    <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-4 mb-2">
                      <h2 className="text-xl sm:text-2xl font-bold text-white">
                        {user?.full_name || 'User'}
                      </h2>
                      <Button
                        variant="outline"
                        size="sm"
                        className="border-reroute-gray text-white hover:bg-reroute-card self-center sm:self-auto"
                        onClick={() => setEditOpen(true)}
                      >
                        <Edit className="w-4 h-4 mr-2" />
                        <span className="hidden sm:inline">Edit Profile</span>
                        <span className="sm:hidden">Edit</span>
                      </Button>
                    </div>
                    <p className="text-gray-400 mb-2 text-sm sm:text-base">
                      {profile?.cycling_experience
                        ? `${profile.cycling_experience} cyclist`
                        : 'Cycling enthusiast'}
                      {profile?.fitness_level &&
                        ` • ${profile.fitness_level} fitness level`}
                    </p>
                    <div className="flex flex-col sm:flex-row sm:items-center space-y-1 sm:space-y-0 sm:space-x-6 text-xs sm:text-sm text-gray-400">
                      <span className="flex items-center justify-center sm:justify-start">
                        <Calendar className="w-4 h-4 mr-1" />
                        <span className="hidden sm:inline">Member since </span>
                        <span className="sm:hidden">Since </span>
                        {profile?.created_at
                          ? new Date(profile.created_at).toLocaleDateString(
                              'en-US',
                              { month: 'short', year: 'numeric' }
                            )
                          : ''}
                      </span>
                      <span className="flex items-center justify-center sm:justify-start">
                        <Activity className="w-4 h-4 mr-1" />
                        {stats.totalActivities} activities
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Tab Navigation */}
            <div className="mb-4 sm:mb-8 flex justify-center sm:justify-start">
              <div className="flex gap-1 sm:gap-2 px-1 sm:px-2 py-2 rounded-xl bg-reroute-tabbar shadow-lg">
                {[
                  { id: 'overview', label: 'Summary', icon: UserIcon },
                  { id: 'stats', label: 'Statistics', icon: TrendingUp },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as 'overview' | 'stats')}
                    className={`flex items-center gap-1 sm:gap-2 px-4 sm:px-6 py-2 rounded-lg font-medium transition-colors text-sm sm:text-base
                      ${
                        activeTab === tab.id
                          ? 'bg-reroute-tab-active text-white shadow'
                          : 'bg-transparent text-white/80 hover:bg-white/10'
                      }
                    `}
                  >
                    <tab.icon
                      className={`w-4 h-4 sm:w-5 sm:h-5 ${activeTab === tab.id ? 'text-white' : 'text-white/80'}`}
                    />
                    <span>{tab.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Content */}
            {activeTab === 'overview' && (
              <div className="space-y-4 sm:space-y-6">
                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-6">
                  {displayStats.map((stat, index) => (
                    <Card
                      key={index}
                      className="bg-reroute-card border-reroute-card hover:shadow-card transition-shadow"
                    >
                      <CardContent className="p-3 sm:p-6">
                        <div className="flex items-center justify-between">
                          <div className="min-w-0 flex-1">
                            <p className="text-xs sm:text-sm font-medium text-gray-400 truncate">
                              {stat.label}
                            </p>
                            <p className="text-lg sm:text-2xl font-bold text-white truncate">
                              {stat.value}
                            </p>
                            {stat.change && (
                              <p className="text-xs sm:text-sm text-reroute-green flex items-center mt-1">
                                <TrendingUp className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                                <span className="truncate">{stat.change}</span>
                              </p>
                            )}
                          </div>
                          <div
                            className={`p-2 sm:p-3 rounded-full ${stat.color} flex-shrink-0 ml-2`}
                          >
                            <div className="w-4 h-4 sm:w-6 sm:h-6">
                              {stat.icon}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Recent Activity */}
                <Card className="bg-reroute-card border-reroute-card">
                  <CardHeader className="pb-3 sm:pb-6">
                    <CardTitle className="flex items-center text-white text-lg sm:text-xl">
                      <Calendar className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
                      Recent Activity
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="space-y-2 sm:space-y-4">
                      {recentActivities.length > 0 ? (
                        recentActivities.map((activity) => (
                          <div
                            key={activity.id}
                            className="flex items-start space-x-3 p-2 sm:p-3 bg-reroute-primary/10 rounded-lg"
                          >
                            <div className="w-2 h-2 bg-reroute-primary rounded-full mt-1.5 flex-shrink-0"></div>
                            <div className="min-w-0 flex-1">
                              <p className="text-sm font-medium text-white truncate">
                                {activity.name}
                              </p>
                              <p className="text-xs text-gray-400">
                                {new Date(
                                  activity.start_date
                                ).toLocaleDateString()}{' '}
                                -{' '}
                                {formatDistance(
                                  activity.distance_m * 0.000621371
                                )}
                              </p>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="text-center py-6 sm:py-8">
                          <p className="text-gray-400 text-sm sm:text-base">
                            No recent activities found...
                          </p>
                          <p className="text-xs sm:text-sm text-gray-500 mt-2">
                            Connect your Strava account to see your activities
                          </p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === 'stats' && (
              <div className="space-y-4 sm:space-y-6">
                {/* Detailed Statistics */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                  <Card className="bg-reroute-card border-reroute-card">
                    <CardHeader className="pb-3 sm:pb-6">
                      <CardTitle className="text-white text-lg sm:text-xl">
                        Performance Overview
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="space-y-3 sm:space-y-4">
                        <div>
                          <div className="flex justify-between text-xs sm:text-sm mb-2">
                            <span className="text-gray-400">
                              Total Distance
                            </span>
                            <span className="text-white">
                              {formatDistance(stats.totalDistance)}
                            </span>
                          </div>
                          <div className="w-full bg-reroute-card rounded-full h-2">
                            <div
                              className="bg-reroute-primary h-2 rounded-full"
                              style={{ width: '100%' }}
                            ></div>
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between text-xs sm:text-sm mb-2">
                            <span className="text-gray-400">Total Time</span>
                            <span className="text-white">
                              {formatTime(stats.totalTime)}
                            </span>
                          </div>
                          <div className="w-full bg-reroute-card rounded-full h-2">
                            <div
                              className="bg-reroute-green h-2 rounded-full"
                              style={{ width: '100%' }}
                            ></div>
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between text-xs sm:text-sm mb-2">
                            <span className="text-gray-400">
                              Total Activities
                            </span>
                            <span className="text-white">
                              {stats.totalActivities}
                            </span>
                          </div>
                          <div className="w-full bg-reroute-card rounded-full h-2">
                            <div
                              className="bg-reroute-purple h-2 rounded-full"
                              style={{ width: '100%' }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-reroute-card border-reroute-card">
                    <CardHeader className="pb-3 sm:pb-6">
                      <CardTitle className="text-white text-lg sm:text-xl">
                        Performance Metrics
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="space-y-3 sm:space-y-4">
                        <div className="flex items-center justify-between p-2 sm:p-3 bg-reroute-primary/10 rounded-lg">
                          <div className="min-w-0">
                            <p className="text-xs sm:text-sm font-medium text-white">
                              Average Speed
                            </p>
                            <p className="text-xs text-gray-400">This month</p>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <p className="text-sm sm:text-lg font-bold text-white">
                              {stats.averageSpeed.toFixed(1)} mph
                            </p>
                            <p className="text-xs text-reroute-green">
                              +2.3 mph
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center justify-between p-2 sm:p-3 bg-reroute-green/10 rounded-lg">
                          <div className="min-w-0">
                            <p className="text-xs sm:text-sm font-medium text-white">
                              Max Distance
                            </p>
                            <p className="text-xs text-gray-400">
                              Single activity
                            </p>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <p className="text-sm sm:text-lg font-bold text-white">
                              {formatDistance(stats.maxDistance)}
                            </p>
                            <p className="text-xs text-reroute-green">
                              +12.8 km
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center justify-between p-2 sm:p-3 bg-reroute-purple/10 rounded-lg">
                          <div className="min-w-0">
                            <p className="text-xs sm:text-sm font-medium text-white">
                              Total Elevation
                            </p>
                            <p className="text-xs text-gray-400">This month</p>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <p className="text-sm sm:text-lg font-bold text-white">
                              {formatElevation(stats.totalElevation)}
                            </p>
                            <p className="text-xs text-reroute-green">+320m</p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}
          </>
        )}

        {sidebarSection === 'subscription' && <SubscriptionSection />}
        {sidebarSection === 'settings' && (
          <div className="text-white [&_label]:text-white [&_p]:text-gray-300 [&_span]:text-gray-300 [&_h1]:text-white [&_h2]:text-white [&_h3]:text-white">
            <SettingsSection />
          </div>
        )}
        <Modal
          isOpen={editOpen}
          onClose={() => setEditOpen(false)}
          title="Edit Profile"
        >
          {user && (
            <EditProfileForm
              user={user}
              onSave={(updatedUser) => {
                setUser(updatedUser);
                setEditOpen(false);
              }}
              onCancel={() => setEditOpen(false)}
            />
          )}
        </Modal>
      </div>
    </div>
  );
};

export default Profile;
