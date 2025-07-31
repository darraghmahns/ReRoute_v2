import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  TrendingUp,
  Play,
  CheckCircle,
  Zap,
  ChevronLeft,
  ChevronRight,
  Heart,
  Dumbbell,
  Activity,
  Zap as ZapIcon,
  RefreshCw,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { trainingService } from '../services/training';
import type { TrainingPlan, Workout, TrainingWeek } from '../types';

interface WorkoutCardProps {
  workout: Workout;
  day: string;
  onClick: () => void;
}

const WorkoutCard: React.FC<WorkoutCardProps> = ({ workout, day, onClick }) => {
  const getWorkoutTypeColor = (type: string) => {
    switch (type) {
      case 'recovery':
        return 'bg-green-500/20 text-green-500 border-green-500/30';
      case 'endurance':
        return 'bg-blue-500/20 text-blue-500 border-blue-500/30';
      case 'threshold':
        return 'bg-cyan-500/20 text-cyan-500 border-cyan-500/30';
      case 'vo2max':
        return 'bg-red-500/20 text-red-500 border-red-500/30';
      case 'cross_training':
        return 'bg-purple-500/20 text-purple-500 border-purple-500/30';
      case 'rest':
        return 'bg-gray-500/20 text-gray-500 border-gray-500/30';
      default:
        return 'bg-gray-500/20 text-gray-500 border-gray-500/30';
    }
  };

  const getWorkoutIcon = (type: string) => {
    switch (type) {
      case 'recovery':
        return <Heart className="w-4 h-4 sm:w-5 sm:h-5" />;
      case 'endurance':
        return <Clock className="w-4 h-4 sm:w-5 sm:h-5" />;
      case 'threshold':
        return <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5" />;
      case 'vo2max':
        return <ZapIcon className="w-4 h-4 sm:w-5 sm:h-5" />;
      case 'cross_training':
        return <Dumbbell className="w-4 h-4 sm:w-5 sm:h-5" />;
      case 'rest':
        return <Heart className="w-4 h-4 sm:w-5 sm:h-5" />;
      default:
        return <Activity className="w-4 h-4 sm:w-5 sm:h-5" />;
    }
  };

  const getWorkoutTypeLabel = (type: string) => {
    switch (type) {
      case 'recovery':
        return 'RECOVERY';
      case 'endurance':
        return 'ENDURANCE';
      case 'threshold':
        return 'THRESHOLD';
      case 'vo2max':
        return 'VO2MAX';
      case 'cross_training':
        return 'CROSS TRAINING';
      case 'rest':
        return 'RECOVERY';
      default:
        return type.toUpperCase();
    }
  };

  return (
    <Card
      className="bg-reroute-card border-reroute-card hover:shadow-card transition-all duration-200 cursor-pointer h-full"
      onClick={onClick}
    >
      <CardContent className="p-3 sm:p-4 relative">
        {/* Icon in top right */}
        <div className="absolute top-2 sm:top-3 right-2 sm:right-3">
          {getWorkoutIcon(workout.workout_type)}
        </div>

        {/* Day */}
        <div className="text-xs sm:text-sm font-medium text-gray-400 mb-1 sm:mb-2 capitalize pr-8">
          {day}
        </div>

        {/* Title */}
        <h3 className="font-semibold text-white text-base sm:text-lg mb-1 sm:mb-2 pr-8 line-clamp-2">
          {workout.title}
        </h3>

        {/* Duration */}
        <div className="text-xs sm:text-sm text-gray-400 mb-1 sm:mb-2">
          {workout.duration_minutes > 0
            ? `${workout.duration_minutes} min`
            : '0 min'}
        </div>

        {/* Description */}
        <p className="text-xs sm:text-sm text-gray-300 mb-2 sm:mb-3 line-clamp-2">
          {workout.description}
        </p>

        {/* Workout Type Badge */}
        <div
          className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getWorkoutTypeColor(workout.workout_type)}`}
        >
          {getWorkoutTypeLabel(workout.workout_type)}
        </div>
      </CardContent>
    </Card>
  );
};

const Training: React.FC = () => {
  const [currentPlan, setCurrentPlan] = useState<TrainingPlan | null>(null);
  const [currentWeekIndex, setCurrentWeekIndex] = useState(0);
  const [selectedWorkout, setSelectedWorkout] = useState<Workout | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [generateForm, setGenerateForm] = useState({
    goal: 'General Fitness',
    weekly_hours: 8,
    fitness_level: 'intermediate',
  });

  useEffect(() => {
    loadPlans();

    // Auto-refresh training plans every 30 seconds when tab is active
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        loadPlans();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const loadPlans = async () => {
    try {
      setLoading(true);
      const userPlans = await trainingService.getPlans();

      // Set the most recent active plan as current (matching AI agent logic)
      // First try to get active plan, then fall back to most recent plan
      let activePlan = userPlans.find((plan) => plan.is_active);
      if (!activePlan && userPlans.length > 0) {
        // Since plans are now ordered by is_active desc, updated_at desc, first plan is the right one
        activePlan = userPlans[0];
      }

      if (activePlan) {
        setCurrentPlan(activePlan);
        console.log(
          'Loaded training plan:',
          activePlan.id,
          'Active:',
          activePlan.is_active
        );
      }
    } catch (error) {
      console.error('Failed to load plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateNewPlan = async () => {
    try {
      setGenerating(true);
      setShowGenerateModal(false); // Close modal immediately

      const newPlan = await trainingService.generatePlan(generateForm);

      setCurrentPlan(newPlan);
      setCurrentWeekIndex(0);
    } catch (error) {
      console.error('Failed to generate plan:', error);
      // Reopen modal on error so user can try again
      setShowGenerateModal(true);
    } finally {
      setGenerating(false);
    }
  };

  const navigateWeek = (direction: 'prev' | 'next') => {
    if (!currentPlan) return;

    const totalWeeks = currentPlan.plan_data.weeks.length;

    if (direction === 'prev' && currentWeekIndex > 0) {
      setCurrentWeekIndex(currentWeekIndex - 1);
    } else if (direction === 'next' && currentWeekIndex < totalWeeks - 1) {
      setCurrentWeekIndex(currentWeekIndex + 1);
    }
  };

  const getCurrentWeek = (): TrainingWeek | null => {
    if (!currentPlan || !currentPlan.plan_data.weeks[currentWeekIndex]) {
      return null;
    }
    return currentPlan.plan_data.weeks[currentWeekIndex];
  };

  const getTotalTrainingTime = (): number => {
    const week = getCurrentWeek();
    if (!week) return 0;

    return Object.values(week.workouts).reduce((total, workout) => {
      return total + workout.duration_minutes;
    }, 0);
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'numeric',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getWeekRange = (): string => {
    const week = getCurrentWeek();
    if (!week) return '';

    const startDate = new Date(week.week_start_date);
    const endDate = new Date(startDate);
    endDate.setDate(startDate.getDate() + 6);

    return `${formatDate(week.week_start_date)} - ${formatDate(endDate.toISOString().split('T')[0])}`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-reroute-primary mx-auto mb-4"></div>
          <p className="text-white">Loading training plans...</p>
        </div>
      </div>
    );
  }

  const currentWeek = getCurrentWeek();

  return (
    <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8 py-4 sm:py-8">
      {/* Header */}
      <div className="mb-4 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-white">Training</h1>
        <p className="text-gray-400 mt-1 sm:mt-2 text-sm sm:text-base">
          AI-powered training plans to improve your cycling
        </p>
      </div>

      {!currentPlan ? (
        /* No Plan State */
        <div className="text-center py-8 sm:py-12 px-4">
          <div className="max-w-md mx-auto">
            <Zap className="w-12 h-12 sm:w-16 sm:h-16 text-reroute-primary mx-auto mb-3 sm:mb-4" />
            <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">
              No Training Plan
            </h2>
            <p className="text-gray-400 mb-4 sm:mb-6 text-sm sm:text-base">
              Generate your first AI-powered training plan to get started with
              structured workouts.
            </p>
            <Button
              onClick={() => setShowGenerateModal(true)}
              className="bg-reroute-primary hover:bg-reroute-primary/80 text-white w-full sm:w-auto"
            >
              Generate Training Plan
            </Button>
          </div>
        </div>
      ) : (
        /* Plan Display */
        <div className="space-y-4 sm:space-y-6">
          {/* Plan Header */}
          <Card className="bg-reroute-card border-reroute-card">
            <CardContent className="p-3 sm:p-6">
              <div className="flex flex-col space-y-4 sm:space-y-0 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex-1">
                  <h2 className="text-xl sm:text-2xl font-bold text-white mb-1 sm:mb-2">
                    {currentPlan.name}
                  </h2>
                  <p className="text-gray-400 text-sm sm:text-base">
                    Training Goal: {currentPlan.goal}
                  </p>
                  {/* Show AI agent updates */}
                  <p className="text-gray-400 text-sm mt-1">
                    Plan ID: {currentPlan.id} | Last updated:{' '}
                    {new Date(currentPlan.updated_at).toLocaleString()}
                  </p>
                  {currentPlan.plan_data?.workout_type && (
                    <p className="text-reroute-primary text-sm mt-1">
                      🤖 AI Update: Workout type set to{' '}
                      {currentPlan.plan_data.workout_type}
                    </p>
                  )}
                  {currentPlan.plan_data?.change_log &&
                    currentPlan.plan_data.change_log.length > 0 && (
                      <p className="text-reroute-primary text-sm mt-1">
                        🤖 Last AI update:{' '}
                        {new Date(
                          currentPlan.plan_data.change_log[
                            currentPlan.plan_data.change_log.length - 1
                          ].timestamp
                        ).toLocaleString()}{' '}
                        -{' '}
                        {
                          currentPlan.plan_data.change_log[
                            currentPlan.plan_data.change_log.length - 1
                          ].field
                        }
                        :{' '}
                        {
                          currentPlan.plan_data.change_log[
                            currentPlan.plan_data.change_log.length - 1
                          ].new_value
                        }
                      </p>
                    )}
                </div>

                <div className="flex flex-col space-y-3 sm:space-y-0 sm:flex-row sm:items-center sm:space-x-6">
                  <div className="grid grid-cols-3 gap-4 sm:flex sm:space-x-6">
                    <div className="text-center">
                      <div className="text-2xl sm:text-3xl font-bold text-white">
                        {Math.round(getTotalTrainingTime() / 60)}h
                      </div>
                      <div className="text-xs sm:text-sm text-gray-400">
                        Total Training Time
                      </div>
                    </div>

                    <div className="text-center">
                      <div className="text-sm sm:text-lg font-semibold text-white">
                        AI Generated
                      </div>
                      <div className="text-xs sm:text-sm text-gray-400">
                        Plan Type
                      </div>
                    </div>

                    <div className="text-center">
                      <div className="text-sm sm:text-lg font-semibold text-white">
                        {formatDate(currentPlan.created_at)}
                      </div>
                      <div className="text-xs sm:text-sm text-gray-400">
                        Plan Date
                      </div>
                    </div>
                  </div>

                  <div className="flex space-x-2 w-full sm:w-auto">
                    <Button
                      onClick={loadPlans}
                      variant="outline"
                      className="border-gray-600 text-gray-300 hover:bg-gray-700 flex-1 sm:flex-none text-sm sm:text-base"
                      size="sm"
                      disabled={loading}
                    >
                      <RefreshCw
                        className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`}
                      />
                      <span className="hidden sm:inline">Refresh</span>
                      <span className="sm:hidden">Refresh</span>
                    </Button>
                    <Button
                      onClick={() => setShowGenerateModal(true)}
                      variant="outline"
                      className="border-gray-600 text-gray-300 hover:bg-gray-700 flex-1 sm:flex-none text-sm sm:text-base"
                      size="sm"
                    >
                      <Calendar className="w-4 h-4 mr-2" />
                      <span className="hidden sm:inline">Regenerate Plan</span>
                      <span className="sm:hidden">Regenerate</span>
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Week Navigation */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-0">
            <Button
              onClick={() => navigateWeek('prev')}
              disabled={currentWeekIndex === 0}
              variant="outline"
              className="border-gray-600 text-gray-300 hover:bg-gray-700 w-full sm:w-auto order-2 sm:order-1"
              size="sm"
            >
              <ChevronLeft className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Previous Week</span>
              <span className="sm:hidden">Previous</span>
            </Button>

            <div className="text-center order-1 sm:order-2">
              <h3 className="text-lg sm:text-xl font-semibold text-white">
                Week {currentWeekIndex + 1}
              </h3>
              <p className="text-gray-400 text-xs sm:text-base">
                {getWeekRange()}
              </p>
            </div>

            <Button
              onClick={() => navigateWeek('next')}
              disabled={
                currentWeekIndex >= currentPlan.plan_data.weeks.length - 1
              }
              variant="outline"
              className="border-gray-600 text-gray-300 hover:bg-gray-700 w-full sm:w-auto order-3"
              size="sm"
            >
              <span className="hidden sm:inline">Next Week</span>
              <span className="sm:hidden">Next</span>
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          </div>

          {/* Weekly Calendar */}
          {currentWeek && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-3 sm:gap-4">
              {Object.entries(currentWeek.workouts).map(([day, workout]) => (
                <WorkoutCard
                  key={workout.id}
                  workout={workout}
                  day={day}
                  onClick={() => setSelectedWorkout(workout)}
                />
              ))}
            </div>
          )}

          {/* Workout Details Dropdown */}
          {selectedWorkout && (
            <Card className="bg-reroute-card border-reroute-card mt-6">
              <CardHeader>
                <CardTitle className="text-white flex items-center justify-between">
                  <span>{selectedWorkout.title}</span>
                  <Button
                    onClick={() => setSelectedWorkout(null)}
                    variant="ghost"
                    size="sm"
                    className="text-gray-400 hover:text-white"
                  >
                    ×
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-white mb-2">
                      Description
                    </h4>
                    <p className="text-gray-300">
                      {selectedWorkout.description}
                    </p>
                  </div>

                  {selectedWorkout.details && (
                    <div>
                      <h4 className="font-semibold text-white mb-2">Details</h4>
                      <p className="text-gray-300">{selectedWorkout.details}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                    <div>
                      <h4 className="font-semibold text-white mb-2 text-sm sm:text-base">
                        Duration
                      </h4>
                      <p className="text-gray-300 text-sm sm:text-base">
                        {selectedWorkout.duration_minutes} minutes
                      </p>
                    </div>

                    {selectedWorkout.ftp_percentage_min &&
                      selectedWorkout.ftp_percentage_max && (
                        <div>
                          <h4 className="font-semibold text-white mb-2 text-sm sm:text-base">
                            FTP Range
                          </h4>
                          <p className="text-gray-300 text-sm sm:text-base">
                            {selectedWorkout.ftp_percentage_min}% -{' '}
                            {selectedWorkout.ftp_percentage_max}%
                          </p>
                        </div>
                      )}
                  </div>

                  <div className="flex items-center space-x-4">
                    <Button
                      onClick={() => {
                        // Mark workout as complete
                        if (currentPlan) {
                          trainingService.markWorkoutComplete(
                            currentPlan.id,
                            selectedWorkout.id,
                            !selectedWorkout.completed
                          );
                          // Update local state
                          setSelectedWorkout({
                            ...selectedWorkout,
                            completed: !selectedWorkout.completed,
                          });
                        }
                      }}
                      className={`${
                        selectedWorkout.completed
                          ? 'bg-green-600 hover:bg-green-700'
                          : 'bg-reroute-primary hover:bg-reroute-primary/80'
                      } text-white`}
                    >
                      {selectedWorkout.completed ? (
                        <>
                          <CheckCircle className="w-4 h-4 mr-2" />
                          Completed
                        </>
                      ) : (
                        <>
                          <Play className="w-4 h-4 mr-2" />
                          Mark Complete
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Training Zones Legend */}
          <Card className="bg-reroute-card border-reroute-card">
            <CardHeader>
              <CardTitle className="text-white">
                Training Zones & Activities
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="text-gray-300">Recovery: &lt;65% FTP</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <span className="text-gray-300">Endurance: 65-85% FTP</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-cyan-500 rounded-full"></div>
                  <span className="text-gray-300">Threshold: 95-105% FTP</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <span className="text-gray-300">VO2max: 110-120% FTP</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                  <span className="text-gray-300">
                    Cross Training: Strength/Other
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Generate Plan Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="bg-reroute-card border-reroute-card w-full max-w-md mx-4">
            <CardHeader>
              <CardTitle className="text-white">
                Generate Training Plan
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Training Goal
                </label>
                <select
                  value={generateForm.goal}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      goal: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-reroute-primary"
                >
                  <option value="General Fitness">General Fitness</option>
                  <option value="Race Preparation">Race Preparation</option>
                  <option value="Weight Loss">Weight Loss</option>
                  <option value="Endurance Building">Endurance Building</option>
                  <option value="Strength Building">Strength Building</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Weekly Hours
                </label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={generateForm.weekly_hours}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      weekly_hours: parseInt(e.target.value),
                    }))
                  }
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-reroute-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Fitness Level
                </label>
                <select
                  value={generateForm.fitness_level}
                  onChange={(e) =>
                    setGenerateForm((prev) => ({
                      ...prev,
                      fitness_level: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-reroute-primary"
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </select>
              </div>

              <div className="flex space-x-3 pt-4">
                <Button
                  onClick={() => setShowGenerateModal(false)}
                  variant="outline"
                  className="flex-1 border-gray-600 text-gray-300 hover:bg-gray-700"
                >
                  Cancel
                </Button>
                <Button
                  onClick={generateNewPlan}
                  disabled={generating}
                  className="flex-1 bg-reroute-primary hover:bg-reroute-primary/80 text-white"
                >
                  {generating ? 'Generating...' : 'Generate Plan'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Global Loading Overlay */}
      {generating && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-reroute-card border border-reroute-card rounded-lg p-8 text-center max-w-md mx-4">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-reroute-primary mx-auto mb-6"></div>
            <h3 className="text-xl font-bold text-white mb-4">
              Generating Your Training Plan
            </h3>
            <p className="text-gray-300 mb-4">
              Our AI is analyzing your Strava data and creating a personalized
              training plan just for you.
            </p>
            <div className="flex items-center justify-center space-x-2 text-sm text-gray-400">
              <div className="animate-pulse">●</div>
              <span>Analyzing your recent activities</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Training;
