import React, { useState, useEffect } from 'react';
import { Calendar, TrendingUp, Target, Clock, Zap, Route, Activity, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useStrava } from '../hooks/useStrava';
import { getCurrentUserWithProfile } from '../services/auth';
import MapboxActivityMap from '../components/MapboxActivityMap';
import { startOfWeek, endOfWeek, isWithinInterval, subWeeks, addWeeks, format } from 'date-fns';

interface StatCardProps {
  title: string;
  value: string;
  change?: string;
  icon: React.ReactNode;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, change, icon, color }) => (
  <Card className="bg-reroute-card border-reroute-card">
    <CardContent className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {change && (
            <p className="text-xs text-green-400 mt-1">{change}</p>
          )}
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          {icon}
        </div>
      </div>
    </CardContent>
  </Card>
);

interface RecentActivity {
  id: string;
  title: string;
  distance: string;
  duration: string;
  date: string;
  elevation?: string;
  type?: string;
  calories?: string;
  average_heartrate?: string;
  map?: { summary_polyline?: string };
}

// Conversion helpers
const metersToMiles = (meters: number) => meters / 1609.34;
const metersToFeet = (meters: number) => meters * 3.28084;

const getMonday = (date: Date) => startOfWeek(date, { weekStartsOn: 1 });
const getSunday = (date: Date) => endOfWeek(date, { weekStartsOn: 1 });

const Dashboard: React.FC = () => {
  const { activities, loading, error, syncActivities } = useStrava();
  const [stravaConnected, setStravaConnected] = useState(false);
  const [expandedActivityId, setExpandedActivityId] = useState<string | null>(null);
  const [selectedWeekStart, setSelectedWeekStart] = useState<Date>(getMonday(new Date()));

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const userData = await getCurrentUserWithProfile();
        setStravaConnected(!!userData.profile?.strava_user_id);
      } catch (error) {
        console.error('Failed to fetch profile:', error);
      }
    };

    fetchProfile();
  }, []);

  // Group activities by week
  const weekStart = selectedWeekStart;
  const weekEnd = getSunday(weekStart);
  const activitiesThisWeek = activities.filter(activity => {
    const activityDate = new Date(activity.start_date);
    return isWithinInterval(activityDate, { start: weekStart, end: weekEnd });
  });

  // Calculate stats from activities
  const calculateStats = () => {
    if (!activitiesThisWeek.length) {
      return {
        weeklyDistance: '0 mi',
        weeklyTime: '0 hrs',
        calories: '0',
        routesCompleted: '0'
      };
    }

    const totalDistanceMiles = activitiesThisWeek.reduce((sum, activity) => sum + metersToMiles(activity.distance_m || 0), 0);
    const totalTime = activitiesThisWeek.reduce((sum, activity) => sum + (activity.moving_time_s || 0), 0) / 3600;
    const totalCalories = activitiesThisWeek.length * 300; // Rough estimate

    return {
      weeklyDistance: `${isNaN(totalDistanceMiles) ? '0.0' : totalDistanceMiles.toFixed(1)} mi`,
      weeklyTime: `${isNaN(totalTime) ? '0.0' : totalTime.toFixed(1)} hrs`,
      calories: totalCalories.toLocaleString(),
      routesCompleted: activitiesThisWeek.length.toString()
    };
  };

  const stats = calculateStats();

  const recentActivities: RecentActivity[] = activitiesThisWeek
    .sort((a, b) => new Date(b.start_date).getTime() - new Date(a.start_date).getTime())
    .slice(0, 10)
    .map(activity => ({
      id: activity.id,
      title: activity.name,
      distance: `${activity.distance_m != null ? metersToMiles(activity.distance_m).toFixed(1) : '0.0'} mi`,
      duration: `${activity.moving_time_s != null ? Math.floor(activity.moving_time_s / 60) : 0}m`,
      elevation: activity.total_elevation_gain_m != null ? `${metersToFeet(activity.total_elevation_gain_m).toFixed(0)} ft` : undefined,
      type: activity?.type || '',
      calories: activity?.calories != null ? `${Math.round(activity.calories)} kcal` : undefined,
      average_heartrate: activity?.average_heartrate != null ? `${Math.round(activity.average_heartrate)} bpm` : undefined,
      date: new Date(activity.start_date).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
      }),
      map: activity.map,
    }));

  return (
    <div className="min-h-full">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white">Dashboard</h1>
              <p className="text-gray-400 mt-2">Welcome back! Here's your cycling overview.</p>
            </div>
            {stravaConnected && (
              <Button
                onClick={syncActivities}
                disabled={loading}
                className="flex items-center gap-2"
              >
                {loading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                Sync Activities
              </Button>
            )}
          </div>
        </div>

        {/* Strava Connection Notice */}
        {!stravaConnected && (
          <Card className="mb-6 bg-yellow-50 border-yellow-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Activity className="w-5 h-5 text-yellow-600" />
                <div>
                  <p className="text-sm font-medium text-yellow-800">
                    Connect to Strava
                  </p>
                  <p className="text-xs text-yellow-600">
                    Connect your Strava account to see your real cycling data and get personalized insights.
                  </p>
                </div>
                <Button size="sm" className="ml-auto">
                  Connect
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Error Message */}
        {error && (
          <Card className="mb-6 bg-red-50 border-red-200">
            <CardContent className="p-4">
              <p className="text-sm text-red-800">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="This Week"
            value={stats.weeklyDistance}
            change="+12% from last week"
            icon={<Activity className="w-6 h-6 text-white" />}
            color="bg-reroute-primary"
          />
          <StatCard
            title="Training Time"
            value={stats.weeklyTime}
            change="+2.3 hrs from last week"
            icon={<Clock className="w-6 h-6 text-white" />}
            color="bg-reroute-green"
          />
          <StatCard
            title="Calories Burned"
            value={stats.calories}
            change="+15% from last week"
            icon={<Zap className="w-6 h-6 text-white" />}
            color="bg-reroute-yellow"
          />
          <StatCard
            title="Activities"
            value={stats.routesCompleted}
            change="+3 from last week"
            icon={<Route className="w-6 h-6 text-white" />}
            color="bg-reroute-purple"
          />
        </div>

        {/* Recent Activities */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="bg-reroute-card border-reroute-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center justify-between">
                <span>Recent Activities</span>
                <div className="flex items-center gap-2">
                  <Button
                    size="icon"
                    className="bg-reroute-primary/20 text-white hover:bg-reroute-primary/40 transition"
                    onClick={() => setSelectedWeekStart(subWeeks(selectedWeekStart, 1))}
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </Button>
                  <span className="text-sm text-gray-300">
                    {format(weekStart, 'MMM d')} - {format(weekEnd, 'MMM d, yyyy')}
                  </span>
                  <Button
                    size="icon"
                    className="bg-reroute-primary/20 text-white hover:bg-reroute-primary/40 transition"
                    onClick={() => setSelectedWeekStart(addWeeks(selectedWeekStart, 1))}
                    disabled={addWeeks(selectedWeekStart, 1) > getMonday(new Date())}
                  >
                    <ChevronRight className="w-5 h-5" />
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="w-6 h-6 animate-spin text-reroute-primary" />
                  <span className="ml-2 text-gray-400">Loading activities...</span>
                </div>
              ) : recentActivities.length > 0 ? (
                <div className="space-y-4">
                  {recentActivities.map((activity) => (
                    <div
                      key={activity.id}
                      className={`flex flex-col cursor-pointer rounded-lg transition-colors ${expandedActivityId === activity.id ? 'bg-reroute-primary/10' : 'bg-reroute-card'}`}
                      onClick={() => setExpandedActivityId(expandedActivityId === activity.id ? null : activity.id)}
                    >
                      <div className="flex items-center justify-between p-3">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-reroute-primary rounded-full flex items-center justify-center">
                            <Activity className="w-5 h-5 text-white" />
                          </div>
                          <div>
                            <p className="text-white font-medium">{activity.title}</p>
                            <p className="text-sm text-gray-400">
                              {activity.distance} • {activity.duration}{activity.elevation ? ` • ${activity.elevation}` : ''}
                              {activity.type ? ` • ${activity.type}` : ''}
                              {activity.calories ? ` • ${activity.calories}` : ''}
                              {activity.average_heartrate ? ` • ${activity.average_heartrate}` : ''}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-gray-400">{activity.date}</p>
                        </div>
                      </div>
                      {expandedActivityId === activity.id && activity.map?.summary_polyline && (
                        <div className="w-full px-3 pb-3">
                          <MapboxActivityMap summary_polyline={activity.map.summary_polyline} height={180} />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-400">No activities yet</p>
                  {!stravaConnected && (
                    <p className="text-sm text-gray-500 mt-2">Connect to Strava to see your activities</p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card className="bg-reroute-card border-reroute-card">
            <CardHeader>
              <CardTitle className="text-white">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-3">
                <Button className="w-full justify-start" variant="outline">
                  <Route className="w-4 h-4 mr-2" />
                  Generate New Route
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <Target className="w-4 h-4 mr-2" />
                  Create Training Plan
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <TrendingUp className="w-4 h-4 mr-2" />
                  View Analytics
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <Calendar className="w-4 h-4 mr-2" />
                  Schedule Workout
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 