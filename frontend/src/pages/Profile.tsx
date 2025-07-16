import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SubscriptionSection from './Subscription';
import SettingsSection from './Settings';
import { User, Trophy, Award, Calendar, MapPin, Clock, TrendingUp, Edit, Camera } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  earned: boolean;
  date?: string;
}

interface Stat {
  label: string;
  value: string;
  change?: string;
  icon: React.ReactNode;
  color: string;
}

const Profile: React.FC = () => {
  const [sidebarSection, setSidebarSection] = useState<'profile' | 'subscription' | 'settings'>('profile');
  const [activeTab, setActiveTab] = useState<'overview' | 'achievements' | 'stats'>('overview');
  const navigate = useNavigate();

  const achievements: Achievement[] = [
    {
      id: '1',
      name: 'First Ride',
      description: 'Complete your first cycling activity',
      icon: '🚴',
      earned: true,
      date: '2024-01-15'
    },
    {
      id: '2',
      name: 'Century Rider',
      description: 'Complete a 100km ride',
      icon: '🏆',
      earned: true,
      date: '2024-02-20'
    },
    {
      id: '3',
      name: 'Hill Climber',
      description: 'Climb 1,000m in a single ride',
      icon: '⛰️',
      earned: false
    },
    {
      id: '4',
      name: 'Consistency King',
      description: 'Ride 7 days in a row',
      icon: '👑',
      earned: true,
      date: '2024-03-10'
    },
    {
      id: '5',
      name: 'Speed Demon',
      description: 'Average 30+ km/h for 50km',
      icon: '⚡',
      earned: false
    },
    {
      id: '6',
      name: 'Explorer',
      description: 'Complete 50 different routes',
      icon: '🗺️',
      earned: false
    }
  ];

  const stats: Stat[] = [
    {
      label: 'Total Distance',
      value: '2,847 km',
      change: '+15% this month',
      icon: <MapPin className="w-6 h-6 text-white" />,
      color: 'bg-reroute-primary'
    },
    {
      label: 'Total Time',
      value: '156 hrs',
      change: '+8% this month',
      icon: <Clock className="w-6 h-6 text-white" />,
      color: 'bg-reroute-green'
    },
    {
      label: 'Activities',
      value: '127',
      change: '+12 this month',
      icon: <Calendar className="w-6 h-6 text-white" />,
      color: 'bg-reroute-purple'
    },
    {
      label: 'Fitness Score',
      value: '85',
      change: '+5 points',
      icon: <TrendingUp className="w-6 h-6 text-white" />,
      color: 'bg-reroute-yellow'
    }
  ];

  const earnedAchievements = achievements.filter(a => a.earned);
  const unearnedAchievements = achievements.filter(a => !a.earned);

  return (
    <div className="flex">
      {/* Sidebar */}
      <aside className="w-56 bg-reroute-card border-r border-reroute-card py-8 hidden md:block">
        <nav className="space-y-2 px-4">
          {[
            { id: 'profile', label: 'Profile' },
            { id: 'subscription', label: 'Subscription' },
            { id: 'settings', label: 'Settings' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setSidebarSection(item.id as 'profile' | 'subscription' | 'settings')}
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
      <div className="flex-1 px-4 sm:px-6 lg:px-8 py-8">
        {/* Back button */}
        <button
          onClick={() => navigate('/')}
          className="mb-4 text-sm text-reroute-primary hover:underline"
        >
          ← Back to Main
        </button>

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white capitalize">{sidebarSection}</h1>
        </div>

        {sidebarSection === 'profile' && (
          <>
            {/* Profile Header */}
            <Card className="mb-8 bg-reroute-card border-reroute-card">
              <CardContent className="p-6">
                <div className="flex items-center space-x-6">
                  <div className="relative">
                    <div className="w-24 h-24 bg-gradient-to-br from-reroute-primary to-reroute-purple rounded-full flex items-center justify-center">
                      <User className="w-12 h-12 text-white" />
                    </div>
                    <button className="absolute -bottom-1 -right-1 p-2 bg-reroute-card rounded-full shadow-card hover:shadow-lg transition-shadow border border-reroute-gray">
                      <Camera className="w-4 h-4 text-gray-400" />
                    </button>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-4 mb-2">
                      <h2 className="text-2xl font-bold text-white">John Doe</h2>
                      <Button variant="outline" size="sm" className="border-reroute-gray text-white hover:bg-reroute-card">
                        <Edit className="w-4 h-4 mr-2" />
                        Edit Profile
                      </Button>
                    </div>
                    <p className="text-gray-400 mb-2">Cycling enthusiast from San Francisco, CA</p>
                    <div className="flex items-center space-x-6 text-sm text-gray-400">
                      <span className="flex items-center">
                        <Calendar className="w-4 h-4 mr-1" />
                        Member since January 2024
                      </span>
                      <span className="flex items-center">
                        <Trophy className="w-4 h-4 mr-1" />
                        {earnedAchievements.length} achievements
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Tab Navigation */}
            <div className="mb-8">
              <div className="border-b border-reroute-card">
                <nav className="-mb-px flex space-x-8">
                  {[
                    { id: 'overview', label: 'Overview', icon: User },
                    { id: 'achievements', label: 'Achievements', icon: Trophy },
                    { id: 'stats', label: 'Statistics', icon: TrendingUp }
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as 'overview' | 'achievements' | 'stats')}
                      className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                        activeTab === tab.id
                          ? 'border-reroute-primary text-reroute-primary'
                          : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-400'
                      }`}
                    >
                      <tab.icon className="w-4 h-4" />
                      <span>{tab.label}</span>
                    </button>
                  ))}
                </nav>
              </div>
            </div>

            {/* Content */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {stats.map((stat, index) => (
                    <Card key={index} className="bg-reroute-card border-reroute-card hover:shadow-card transition-shadow">
                      <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-gray-400">{stat.label}</p>
                            <p className="text-2xl font-bold text-white">{stat.value}</p>
                            {stat.change && (
                              <p className="text-sm text-reroute-green flex items-center mt-1">
                                <TrendingUp className="w-4 h-4 mr-1" />
                                {stat.change}
                              </p>
                            )}
                          </div>
                          <div className={`p-3 rounded-full ${stat.color}`}>
                            {stat.icon}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Recent Activity */}
                <Card className="bg-reroute-card border-reroute-card">
                  <CardHeader>
                    <CardTitle className="flex items-center text-white">
                      <Calendar className="w-5 h-5 mr-2" />
                      Recent Activity
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center space-x-3 p-3 bg-reroute-primary/10 rounded-lg">
                        <div className="w-2 h-2 bg-reroute-primary rounded-full"></div>
                        <div>
                          <p className="text-sm font-medium text-white">Morning Training Ride</p>
                          <p className="text-xs text-gray-400">Today, 7:30 AM - 45.2 km</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3 p-3 bg-reroute-green/10 rounded-lg">
                        <div className="w-2 h-2 bg-reroute-green rounded-full"></div>
                        <div>
                          <p className="text-sm font-medium text-white">Interval Training</p>
                          <p className="text-xs text-gray-400">Yesterday, 6:15 PM - 25.8 km</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3 p-3 bg-reroute-purple/10 rounded-lg">
                        <div className="w-2 h-2 bg-reroute-purple rounded-full"></div>
                        <div>
                          <p className="text-sm font-medium text-white">Scenic Route - Lake Loop</p>
                          <p className="text-xs text-gray-400">2 days ago - 68.4 km</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === 'achievements' && (
              <div className="space-y-6">
                {/* Earned Achievements */}
                <Card className="bg-reroute-card border-reroute-card">
                  <CardHeader>
                    <CardTitle className="flex items-center text-white">
                      <Trophy className="w-5 h-5 mr-2" />
                      Earned Achievements ({earnedAchievements.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {earnedAchievements.map((achievement) => (
                        <div key={achievement.id} className="p-4 bg-reroute-card/50 rounded-lg border border-reroute-green/20">
                          <div className="flex items-center space-x-3">
                            <div className="text-2xl">{achievement.icon}</div>
                            <div>
                              <h4 className="font-medium text-white">{achievement.name}</h4>
                              <p className="text-sm text-gray-400">{achievement.description}</p>
                              {achievement.date && (
                                <p className="text-xs text-reroute-green mt-1">Earned {achievement.date}</p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Unearned Achievements */}
                <Card className="bg-reroute-card border-reroute-card">
                  <CardHeader>
                    <CardTitle className="flex items-center text-white">
                      <Award className="w-5 h-5 mr-2" />
                      Available Achievements ({unearnedAchievements.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {unearnedAchievements.map((achievement) => (
                        <div key={achievement.id} className="p-4 bg-reroute-card/50 rounded-lg border border-reroute-card opacity-60">
                          <div className="flex items-center space-x-3">
                            <div className="text-2xl opacity-50">{achievement.icon}</div>
                            <div>
                              <h4 className="font-medium text-gray-400">{achievement.name}</h4>
                              <p className="text-sm text-gray-500">{achievement.description}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === 'stats' && (
              <div className="space-y-6">
                {/* Detailed Statistics */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <Card className="bg-reroute-card border-reroute-card">
                    <CardHeader>
                      <CardTitle className="text-white">Monthly Progress</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div>
                          <div className="flex justify-between text-sm mb-2">
                            <span className="text-gray-400">Distance</span>
                            <span className="text-white">285 km / 300 km</span>
                          </div>
                          <div className="w-full bg-reroute-card rounded-full h-2">
                            <div className="bg-reroute-primary h-2 rounded-full" style={{ width: '95%' }}></div>
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between text-sm mb-2">
                            <span className="text-gray-400">Time</span>
                            <span className="text-white">18 hrs / 20 hrs</span>
                          </div>
                          <div className="w-full bg-reroute-card rounded-full h-2">
                            <div className="bg-reroute-green h-2 rounded-full" style={{ width: '90%' }}></div>
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between text-sm mb-2">
                            <span className="text-gray-400">Activities</span>
                            <span className="text-white">12 / 15</span>
                          </div>
                          <div className="w-full bg-reroute-card rounded-full h-2">
                            <div className="bg-reroute-purple h-2 rounded-full" style={{ width: '80%' }}></div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-reroute-card border-reroute-card">
                    <CardHeader>
                      <CardTitle className="text-white">Performance Trends</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between p-3 bg-reroute-primary/10 rounded-lg">
                          <div>
                            <p className="text-sm font-medium text-white">Average Speed</p>
                            <p className="text-xs text-gray-400">This month</p>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-bold text-white">28.5 km/h</p>
                            <p className="text-xs text-reroute-green">+2.3 km/h</p>
                          </div>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-reroute-green/10 rounded-lg">
                          <div>
                            <p className="text-sm font-medium text-white">Max Distance</p>
                            <p className="text-xs text-gray-400">This month</p>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-bold text-white">85.2 km</p>
                            <p className="text-xs text-reroute-green">+12.8 km</p>
                          </div>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-reroute-purple/10 rounded-lg">
                          <div>
                            <p className="text-sm font-medium text-white">Total Elevation</p>
                            <p className="text-xs text-gray-400">This month</p>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-bold text-white">2,450m</p>
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
      </div>
    </div>
  );
};

export default Profile; 