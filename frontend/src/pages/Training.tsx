import React, { useState } from 'react';
import { Calendar, Clock, Target, TrendingUp, Play, CheckCircle, Award, BookOpen, Zap } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

interface Workout {
  id: string;
  name: string;
  description: string;
  duration: string;
  intensity: 'Low' | 'Medium' | 'High';
  type: 'Endurance' | 'Interval' | 'Strength' | 'Recovery';
  completed: boolean;
  scheduled: string;
  calories: number;
  distance?: string;
}

interface TrainingPlan {
  id: string;
  name: string;
  description: string;
  duration: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  workouts: Workout[];
  progress: number;
}

const Training: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'plans' | 'sessions' | 'progress'>('plans');

  const trainingPlans: TrainingPlan[] = [
    {
      id: '1',
      name: 'Beginner Foundation',
      description: 'Build your cycling foundation with structured workouts',
      duration: '8 weeks',
      difficulty: 'Beginner',
      progress: 65,
      workouts: [
        {
          id: 'w1',
          name: 'Easy Ride',
          description: 'Gentle 30-minute ride to build endurance',
          duration: '30 min',
          intensity: 'Low',
          type: 'Endurance',
          completed: true,
          scheduled: 'Today',
          calories: 180
        },
        {
          id: 'w2',
          name: 'Interval Training',
          description: 'Short bursts of high intensity followed by recovery',
          duration: '45 min',
          intensity: 'High',
          type: 'Interval',
          completed: false,
          scheduled: 'Tomorrow',
          calories: 320
        }
      ]
    },
    {
      id: '2',
      name: 'Advanced Performance',
      description: 'Push your limits with high-intensity training',
      duration: '12 weeks',
      difficulty: 'Advanced',
      progress: 45,
      workouts: [
        {
          id: 'w3',
          name: 'Hill Climbs',
          description: 'Repeated hill climbs to build strength',
          duration: '60 min',
          intensity: 'High',
          type: 'Strength',
          completed: false,
          scheduled: 'Today',
          calories: 450,
          distance: '25 km'
        }
      ]
    }
  ];

  const todayWorkouts: Workout[] = [
    {
      id: 'today1',
      name: 'Morning Endurance',
      description: 'Steady pace ride to build aerobic capacity',
      duration: '45 min',
      intensity: 'Medium',
      type: 'Endurance',
      completed: false,
      scheduled: '9:00 AM',
      calories: 280
    },
    {
      id: 'today2',
      name: 'Recovery Ride',
      description: 'Easy ride to promote recovery',
      duration: '30 min',
      intensity: 'Low',
      type: 'Recovery',
      completed: false,
      scheduled: '6:00 PM',
      calories: 150
    }
  ];

  const getIntensityColor = (intensity: string) => {
    switch (intensity) {
      case 'Low': return 'bg-reroute-green/20 text-reroute-green';
      case 'Medium': return 'bg-reroute-yellow/20 text-reroute-yellow';
      case 'High': return 'bg-reroute-red/20 text-reroute-red';
      default: return 'bg-reroute-card text-gray-400';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'Endurance': return 'bg-reroute-primary/20 text-reroute-primary';
      case 'Interval': return 'bg-reroute-purple/20 text-reroute-purple';
      case 'Strength': return 'bg-reroute-yellow/20 text-reroute-yellow';
      case 'Recovery': return 'bg-reroute-green/20 text-reroute-green';
      default: return 'bg-reroute-card text-gray-400';
    }
  };

  return (
    <div className="min-h-full">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Training</h1>
          <p className="text-gray-400 mt-2">Structured workouts and training plans to improve your cycling</p>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="border-b border-reroute-card">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'plans', label: 'Training Plans', icon: BookOpen },
                { id: 'sessions', label: 'Today\'s Sessions', icon: Calendar },
                { id: 'progress', label: 'Progress', icon: TrendingUp }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as 'plans' | 'sessions' | 'progress')}
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
        {activeTab === 'plans' && (
          <div className="space-y-6">
            {/* AI Recommendations */}
            <Card className="bg-reroute-card border-reroute-card">
              <CardHeader>
                <CardTitle className="flex items-center text-white">
                  <Zap className="w-5 h-5 mr-2 text-reroute-yellow" />
                  AI Training Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-gradient-to-r from-reroute-primary/10 to-reroute-purple/10 p-4 rounded-lg">
                  <p className="text-sm text-gray-300 mb-3">
                    Based on your recent performance, we recommend focusing on endurance training this week.
                  </p>
                  <Button size="sm" className="bg-reroute-primary hover:bg-reroute-primary/80 text-white">
                    View Recommendations
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Training Plans */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {trainingPlans.map((plan) => (
                <Card key={plan.id} className="bg-reroute-card border-reroute-card hover:shadow-card transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-white text-lg mb-2">{plan.name}</CardTitle>
                        <p className="text-sm text-gray-400 mb-3">{plan.description}</p>
                        <div className="flex items-center space-x-4 text-sm text-gray-400">
                          <div className="flex items-center">
                            <Clock className="w-4 h-4 mr-1" />
                            {plan.duration}
                          </div>
                          <div className="flex items-center">
                            <Target className="w-4 h-4 mr-1" />
                            {plan.difficulty}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-white">{plan.progress}%</div>
                        <div className="text-sm text-gray-400">Complete</div>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent>
                    {/* Progress Bar */}
                    <div className="mb-4">
                      <div className="w-full bg-reroute-card rounded-full h-2">
                        <div 
                          className="bg-reroute-primary h-2 rounded-full transition-all duration-300" 
                          style={{ width: `${plan.progress}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* Workouts */}
                    <div className="space-y-3">
                      {plan.workouts.map((workout) => (
                        <div key={workout.id} className="flex items-center justify-between p-3 bg-reroute-card/50 rounded-lg">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <h4 className="font-medium text-white">{workout.name}</h4>
                              {workout.completed && (
                                <CheckCircle className="w-4 h-4 text-reroute-green" />
                              )}
                            </div>
                            <p className="text-sm text-gray-400">{workout.description}</p>
                            <div className="flex items-center space-x-4 mt-2">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getIntensityColor(workout.intensity)}`}>
                                {workout.intensity}
                              </span>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(workout.type)}`}>
                                {workout.type}
                              </span>
                              <span className="text-sm text-gray-400">{workout.duration}</span>
                            </div>
                          </div>
                          <Button size="sm" className="bg-reroute-primary hover:bg-reroute-primary/80 text-white">
                            <Play className="w-4 h-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'sessions' && (
          <div className="space-y-6">
            {/* Today's Schedule */}
            <Card className="bg-reroute-card border-reroute-card">
              <CardHeader>
                <CardTitle className="flex items-center text-white">
                  <Calendar className="w-5 h-5 mr-2" />
                  Today's Training Sessions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {todayWorkouts.map((workout) => (
                    <div key={workout.id} className="flex items-center justify-between p-4 bg-reroute-card/50 rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h4 className="font-medium text-white">{workout.name}</h4>
                          {workout.completed && (
                            <CheckCircle className="w-4 h-4 text-reroute-green" />
                          )}
                        </div>
                        <p className="text-sm text-gray-400 mt-1">{workout.description}</p>
                        <div className="flex items-center space-x-4 mt-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getIntensityColor(workout.intensity)}`}>
                            {workout.intensity}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(workout.type)}`}>
                            {workout.type}
                          </span>
                          <span className="text-sm text-gray-400">{workout.duration}</span>
                          <span className="text-sm text-gray-400">{workout.scheduled}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-400">{workout.calories} cal</div>
                        <Button size="sm" className="mt-2 bg-reroute-primary hover:bg-reroute-primary/80 text-white">
                          Start
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'progress' && (
          <div className="space-y-6">
            {/* Progress Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="bg-reroute-card border-reroute-card">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-400">This Week</p>
                      <p className="text-2xl font-bold text-white">12 hrs</p>
                      <p className="text-sm text-reroute-green">+2.5 hrs</p>
                    </div>
                    <div className="p-3 rounded-full bg-reroute-primary">
                      <Clock className="w-6 h-6 text-white" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-reroute-card border-reroute-card">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-400">Workouts</p>
                      <p className="text-2xl font-bold text-white">8</p>
                      <p className="text-sm text-reroute-green">+2</p>
                    </div>
                    <div className="p-3 rounded-full bg-reroute-green">
                      <Target className="w-6 h-6 text-white" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-reroute-card border-reroute-card">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-400">Fitness Score</p>
                      <p className="text-2xl font-bold text-white">85</p>
                      <p className="text-sm text-reroute-green">+5</p>
                    </div>
                    <div className="p-3 rounded-full bg-reroute-purple">
                      <Award className="w-6 h-6 text-white" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Achievements */}
            <Card className="bg-reroute-card border-reroute-card">
              <CardHeader>
                <CardTitle className="flex items-center text-white">
                  <Award className="w-5 h-5 mr-2" />
                  Recent Achievements
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center space-x-3 p-3 bg-reroute-primary/10 rounded-lg">
                    <div className="w-2 h-2 bg-reroute-primary rounded-full"></div>
                    <div>
                      <p className="text-sm font-medium text-white">Completed 5 workouts this week</p>
                      <p className="text-xs text-gray-400">2 days ago</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3 p-3 bg-reroute-green/10 rounded-lg">
                    <div className="w-2 h-2 bg-reroute-green rounded-full"></div>
                    <div>
                      <p className="text-sm font-medium text-white">Improved endurance by 15%</p>
                      <p className="text-xs text-gray-400">1 week ago</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3 p-3 bg-reroute-purple/10 rounded-lg">
                    <div className="w-2 h-2 bg-reroute-purple rounded-full"></div>
                    <div>
                      <p className="text-sm font-medium text-white">Reached 1000 total training hours</p>
                      <p className="text-xs text-gray-400">2 weeks ago</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default Training; 