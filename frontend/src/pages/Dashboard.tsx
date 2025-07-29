import React, { useState, useEffect } from 'react';
import {
  Calendar,
  TrendingUp,
  Target,
  Clock,
  Zap,
  Route,
  Activity,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useStrava } from '../hooks/useStrava';
import { getCurrentUserWithProfile } from '../services/auth';
import MapboxActivityMap from '../components/MapboxActivityMap';
import {
  startOfWeek,
  endOfWeek,
  isWithinInterval,
  subWeeks,
  addWeeks,
  format,
} from 'date-fns';

interface StatCardProps {
  title: string;
  value: string;
  change?: string;
  icon: React.ReactNode;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  icon,
  color,
}) => {
  // Determine if the change is positive, negative, or neutral
  const isPositive = change && change.includes('+');
  const isNegative = change && change.includes('-');

  return (
    <Card className="bg-reroute-card border-reroute-card">
      <CardContent className="p-3 sm:p-6">
        <div className="flex items-center justify-between">
          <div className="min-w-0 flex-1">
            <p className="text-xs sm:text-sm font-medium text-gray-400 truncate">{title}</p>
            <p className="text-lg sm:text-2xl font-bold text-white truncate">{value}</p>
            {change && (
              <p
                className={`text-xs mt-1 ${
                  isPositive
                    ? 'text-green-400'
                    : isNegative
                      ? 'text-red-400'
                      : 'text-gray-400'
                }`}
              >
                {change}
              </p>
            )}
          </div>
          <div className={`p-2 sm:p-3 rounded-full ${color} flex-shrink-0 ml-2`}>{icon}</div>
        </div>
      </CardContent>
    </Card>
  );
};

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
  const [expandedActivityId, setExpandedActivityId] = useState<string | null>(
    null
  );
  const [selectedWeekStart, setSelectedWeekStart] = useState<Date>(
    getMonday(new Date())
  );

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
  const previousWeekStart = subWeeks(weekStart, 1);
  const previousWeekEnd = getSunday(previousWeekStart);

  const activitiesThisWeek = activities.filter((activity) => {
    const activityDate = new Date(activity.start_date);
    return isWithinInterval(activityDate, { start: weekStart, end: weekEnd });
  });

  const activitiesPreviousWeek = activities.filter((activity) => {
    const activityDate = new Date(activity.start_date);
    return isWithinInterval(activityDate, {
      start: previousWeekStart,
      end: previousWeekEnd,
    });
  });

  // Calculate stats from activities
  const calculateStats = () => {
    if (!activitiesThisWeek.length) {
      return {
        weeklyDistance: '0 mi',
        weeklyTime: '0 hrs',
        calories: '0',
        routesCompleted: '0',
        distanceChange: '0%',
        timeChange: '0 hrs',
        caloriesChange: '0%',
        activitiesChange: '0',
      };
    }

    const totalDistanceMiles = activitiesThisWeek.reduce(
      (sum, activity) => sum + metersToMiles(activity.distance_m || 0),
      0
    );
    const totalTime = activitiesThisWeek.reduce(
      (sum, activity) => sum + (activity.moving_time_s || 0) / 3600,
      0
    );
    const totalCalories = activitiesThisWeek.reduce(
      (sum, activity) => sum + (activity.calories || 300),
      0
    );

    // Calculate previous week stats for comparison
    const prevDistanceMiles = activitiesPreviousWeek.reduce(
      (sum, activity) => sum + metersToMiles(activity.distance_m || 0),
      0
    );
    const prevTime = activitiesPreviousWeek.reduce(
      (sum, activity) => sum + (activity.moving_time_s || 0) / 3600,
      0
    );
    const prevCalories = activitiesPreviousWeek.reduce(
      (sum, activity) => sum + (activity.calories || 300),
      0
    );

    // Calculate percentage changes
    const distanceChange =
      prevDistanceMiles > 0
        ? ((totalDistanceMiles - prevDistanceMiles) / prevDistanceMiles) * 100
        : 0;
    const timeChange = prevTime > 0 ? totalTime - prevTime : 0; // Show hours difference, not percentage
    const caloriesChange =
      prevCalories > 0
        ? ((totalCalories - prevCalories) / prevCalories) * 10
        : 0;
    const activitiesChange =
      activitiesPreviousWeek.length > 0
        ? activitiesThisWeek.length - activitiesPreviousWeek.length
        : activitiesThisWeek.length;

    return {
      weeklyDistance: `${isNaN(totalDistanceMiles) ? '0.0' : totalDistanceMiles.toFixed(1)} mi`,
      weeklyTime: `${isNaN(totalTime) ? '0.0' : totalTime.toFixed(1)} hrs`,
      calories: totalCalories.toLocaleString(),
      routesCompleted: activitiesThisWeek.length.toString(),
      distanceChange: `${distanceChange >= 0 ? '+' : ''}${distanceChange.toFixed(1)}%`,
      timeChange: `${timeChange >= 0 ? '+' : ''}${timeChange.toFixed(1)} hrs`,
      caloriesChange: `${caloriesChange >= 0 ? '+' : ''}${caloriesChange.toFixed(1)}%`,
      activitiesChange: `${activitiesChange >= 0 ? '+' : ''}${activitiesChange.toString()}`,
    };
  };

  const stats = calculateStats();

  const recentActivities: RecentActivity[] = activitiesThisWeek
    .sort(
      (a, b) =>
        new Date(b.start_date).getTime() - new Date(a.start_date).getTime()
    )
    .slice(0, 10)
    .map((activity) => ({
      id: activity.id,
      title: activity.name,
      distance: `${activity.distance_m != null ? metersToMiles(activity.distance_m).toFixed(1) : '0.0'} mi`,
      duration: `${activity.moving_time_s != null ? Math.floor(activity.moving_time_s / 60) : 0}m`,
      elevation:
        activity.total_elevation_gain_m != null
          ? `${metersToFeet(activity.total_elevation_gain_m).toFixed(0)} ft`
          : undefined,
      type: activity?.type || '',
      calories:
        activity?.calories != null
          ? `${Math.round(activity.calories)} kcal`
          : undefined,
      average_heartrate:
        activity?.average_heartrate != null
          ? `${Math.round(activity.average_heartrate)} bpm`
          : undefined,
      date: new Date(activity.start_date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      }),
      map: activity.map,
    }));

  return (
    <div className="">
      <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8 py-4 sm:py-8">
        {/* Header */}
        <div className="mb-4 sm:mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-white">Dashboard</h1>
              <p className="text-gray-400 mt-1 sm:mt-2 text-sm sm:text-base">
                Welcome back! Here's your cycling overview.
              </p>
            </div>
            {stravaConnected && (
              <Button
                onClick={syncActivities}
                disabled={loading}
                className="flex items-center gap-2 text-white w-full sm:w-auto justify-center"
                size="sm"
              >
                {loading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                <span className="sm:inline">Sync Activities</span>
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
                    Connect your Strava account to see your real cycling data
                    and get personalized insights.
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
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-6 mb-4 sm:mb-8">
          <StatCard
            title="This Week"
            value={stats.weeklyDistance}
            change={stats.distanceChange}
            icon={<Activity className="w-4 h-4 sm:w-6 sm:h-6 text-white" />}
            color="bg-reroute-primary"
          />
          <StatCard
            title="Training Time"
            value={stats.weeklyTime}
            change={stats.timeChange}
            icon={<Clock className="w-4 h-4 sm:w-6 sm:h-6 text-white" />}
            color="bg-reroute-green"
          />
          <StatCard
            title="Calories Burned"
            value={stats.calories}
            change={stats.caloriesChange}
            icon={<Zap className="w-4 h-4 sm:w-6 sm:h-6 text-white" />}
            color="bg-reroute-yellow"
          />
          <StatCard
            title="Activities"
            value={stats.routesCompleted}
            change={stats.activitiesChange}
            icon={<Route className="w-4 h-4 sm:w-6 sm:h-6 text-white" />}
            color="bg-reroute-purple"
          />
        </div>

        {/* Recent Activities */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-6">
          <Card className="bg-reroute-card border-reroute-card">
            <CardHeader className="pb-3 sm:pb-6">
              <CardTitle className="text-white flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <span className="text-lg sm:text-xl">Recent Activities</span>
                <div className="flex items-center gap-1 sm:gap-2 justify-center sm:justify-end">
                  <Button
                    size="icon"
                    className="bg-reroute-primary/20 text-white hover:bg-reroute-primary/40 transition h-8 w-8 sm:h-10 sm:w-10"
                    onClick={() =>
                      setSelectedWeekStart(subWeeks(selectedWeekStart, 1))
                    }
                  >
                    <ChevronLeft className="w-4 h-4 sm:w-5 sm:h-5" />
                  </Button>
                  <span className="text-xs sm:text-sm text-gray-300 px-2 text-center">
                    {format(weekStart, 'MMM d')} -{' '}
                    {format(weekEnd, 'MMM d, yyyy')}
                  </span>
                  <Button
                    size="icon"
                    className="bg-reroute-primary/20 text-white hover:bg-reroute-primary/40 transition h-8 w-8 sm:h-10 sm:w-10"
                    onClick={() =>
                      setSelectedWeekStart(addWeeks(selectedWeekStart, 1))
                    }
                    disabled={
                      addWeeks(selectedWeekStart, 1) > getMonday(new Date())
                    }
                  >
                    <ChevronRight className="w-4 h-4 sm:w-5 sm:h-5" />
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {loading ? (
                <div className="flex items-center justify-center py-6 sm:py-8">
                  <RefreshCw className="w-5 h-5 sm:w-6 sm:h-6 animate-spin text-reroute-primary" />
                  <span className="ml-2 text-gray-400 text-sm sm:text-base">
                    Loading activities...
                  </span>
                </div>
              ) : recentActivities.length > 0 ? (
                <div className="space-y-2 sm:space-y-4">
                  {recentActivities.map((activity) => (
                    <div
                      key={activity.id}
                      className={`flex flex-col cursor-pointer rounded-lg transition-colors ${expandedActivityId === activity.id ? 'bg-reroute-primary/10' : 'bg-reroute-card'}`}
                      onClick={() =>
                        setExpandedActivityId(
                          expandedActivityId === activity.id
                            ? null
                            : activity.id
                        )
                      }
                    >
                      <div className="flex items-start sm:items-center gap-3 p-2 sm:p-3">
                        <div className="w-8 h-8 sm:w-10 sm:h-10 bg-reroute-primary rounded-full flex items-center justify-center flex-shrink-0">
                          <Activity className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start sm:items-center gap-2 mb-1">
                            <p className="text-white font-medium text-sm sm:text-base truncate flex-1">
                              {activity.title}
                            </p>
                            <a
                              href={`https://www.strava.com/activities/${activity.id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="text-gray-400 hover:text-reroute-primary transition-colors flex-shrink-0"
                              title="View on Strava"
                            >
                              <ExternalLink className="w-3 h-3 sm:w-4 sm:h-4" />
                            </a>
                          </div>
                          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-0">
                            <p className="text-xs sm:text-sm text-gray-400 truncate">
                              {activity.distance} • {activity.duration}
                              {activity.elevation && window.innerWidth > 640
                                ? ` • ${activity.elevation}`
                                : ''}
                              {activity.type && window.innerWidth > 640 ? ` • ${activity.type}` : ''}
                              {activity.calories && window.innerWidth > 768
                                ? ` • ${activity.calories}`
                                : ''}
                              {activity.average_heartrate && window.innerWidth > 768
                                ? ` • ${activity.average_heartrate}`
                                : ''}
                            </p>
                            <p className="text-xs sm:text-sm text-gray-400 flex-shrink-0">
                              {activity.date}
                            </p>
                          </div>
                        </div>
                      </div>
                      {expandedActivityId === activity.id &&
                        activity.map?.summary_polyline && (
                          <div className="w-full px-2 sm:px-3 pb-2 sm:pb-3">
                            <MapboxActivityMap
                              summary_polyline={activity.map.summary_polyline}
                              height={window.innerWidth < 640 ? 120 : 180}
                            />
                          </div>
                        )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 sm:py-8">
                  <Activity className="w-8 h-8 sm:w-12 sm:h-12 text-gray-400 mx-auto mb-3 sm:mb-4" />
                  <p className="text-gray-400 text-sm sm:text-base">No activities yet</p>
                  {!stravaConnected && (
                    <p className="text-xs sm:text-sm text-gray-500 mt-2">
                      Connect to Strava to see your activities
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card className="bg-reroute-card border-reroute-card">
            <CardHeader className="pb-3 sm:pb-6">
              <CardTitle className="text-white text-lg sm:text-xl">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="grid grid-cols-1 gap-2 sm:gap-3">
                <Button
                  className="w-full justify-start text-white text-sm sm:text-base h-10 sm:h-auto"
                  variant="outline"
                >
                  <Route className="w-4 h-4 mr-2 flex-shrink-0" />
                  <span className="truncate">Generate New Route</span>
                </Button>
                <Button
                  className="w-full justify-start text-white text-sm sm:text-base h-10 sm:h-auto"
                  variant="outline"
                >
                  <Target className="w-4 h-4 mr-2 flex-shrink-0" />
                  <span className="truncate">Create Training Plan</span>
                </Button>
                <Button
                  className="w-full justify-start text-white text-sm sm:text-base h-10 sm:h-auto"
                  variant="outline"
                >
                  <TrendingUp className="w-4 h-4 mr-2 flex-shrink-0" />
                  <span className="truncate">View Analytics</span>
                </Button>
                <Button
                  className="w-full justify-start text-white text-sm sm:text-base h-10 sm:h-auto"
                  variant="outline"
                >
                  <Calendar className="w-4 h-4 mr-2 flex-shrink-0" />
                  <span className="truncate">Schedule Workout</span>
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
