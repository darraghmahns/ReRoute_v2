import React, { useState, useEffect } from 'react';
import { Calendar, Clock, Target, TrendingUp, Play, CheckCircle, Award, BookOpen, Zap, ChevronLeft, ChevronRight, Heart, Dumbbell, Activity, Zap as ZapIcon } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { trainingService } from '../services/training';
import { TrainingPlan, Workout, TrainingWeek } from '../types';

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
        return <Heart className="w-5 h-5" />;
      case 'endurance':
        return <Clock className="w-5 h-5" />;
      case 'threshold':
        return <TrendingUp className="w-5 h-5" />;
      case 'vo2max':
        return <ZapIcon className="w-5 h-5" />;
      case 'cross_training':
        return <Dumbbell className="w-5 h-5" />;
      case 'rest':
        return <Heart className="w-5 h-5" />;
      default:
        return <Activity className="w-5 h-5" />;
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
      <CardContent className="p-4 relative">
        {/* Icon in top right */}
        <div className="absolute top-3 right-3">
          {getWorkoutIcon(workout.workout_type)}
        </div>
        
        {/* Day */}
        <div className="text-sm font-medium text-gray-400 mb-2 capitalize">
          {day}
        </div>
        
        {/* Title */}
        <h3 className="font-semibold text-white text-lg mb-2">
          {workout.title}
        </h3>
        
        {/* Duration */}
        <div className="text-sm text-gray-400 mb-2">
          {workout.duration_minutes > 0 ? `${workout.duration_minutes} min` : '0 min'}
        </div>
        
        {/* Description */}
        <p className="text-sm text-gray-300 mb-3 line-clamp-2">
          {workout.description}
        </p>
        
        {/* Workout Type Badge */}
        <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getWorkoutTypeColor(workout.workout_type)}`}>
          {getWorkoutTypeLabel(workout.workout_type)}
        </div>
      </CardContent>
    </Card>
  );
};

const Training: React.FC = () => {
  const [plans, setPlans] = useState<TrainingPlan[]>([]);
  const [currentPlan, setCurrentPlan] = useState<TrainingPlan | null>(null);
  const [currentWeekIndex, setCurrentWeekIndex] = useState(0);
  const [selectedWorkout, setSelectedWorkout] = useState<Workout | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [generateForm, setGenerateForm] = useState({
    goal: 'General Fitness',
    weekly_hours: 8,
    fitness_level: 'intermediate'
  });

  useEffect(() => {
    loadPlans();
  }, []);

  const loadPlans = async () => {
    try {
      setLoading(true);
      const userPlans = await trainingService.getPlans();
      setPlans(userPlans);
      
      // Set the most recent active plan as current
      const activePlan = userPlans.find(plan => plan.is_active) || userPlans[0];
      if (activePlan) {
        setCurrentPlan(activePlan);
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
      const newPlan = await trainingService.generatePlan(generateForm);
      setPlans(prev => [newPlan, ...prev]);
      setCurrentPlan(newPlan);
      setCurrentWeekIndex(0);
      setShowGenerateModal(false);
    } catch (error) {
      console.error('Failed to generate plan:', error);
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
      year: 'numeric' 
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Training</h1>
        <p className="text-gray-400 mt-2">AI-powered training plans to improve your cycling</p>
      </div>

      {!currentPlan ? (
        /* No Plan State */
        <div className="text-center py-12">
          <div className="max-w-md mx-auto">
            <Zap className="w-16 h-16 text-reroute-primary mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-4">No Training Plan</h2>
            <p className="text-gray-400 mb-6">
              Generate your first AI-powered training plan to get started with structured workouts.
            </p>
            <Button 
              onClick={() => setShowGenerateModal(true)}
              className="bg-reroute-primary hover:bg-reroute-primary/80 text-white"
            >
              Generate Training Plan
            </Button>
          </div>
        </div>
      ) : (
        /* Plan Display */
        <div className="space-y-6">
          {/* Plan Header */}
          <Card className="bg-reroute-card border-reroute-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-white mb-2">{currentPlan.name}</h2>
                  <p className="text-gray-400">Training Goal: {currentPlan.goal}</p>
                </div>
                
                <div className="flex items-center space-x-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-white">{Math.round(getTotalTrainingTime() / 60)}h</div>
                    <div className="text-sm text-gray-400">Total Training Time</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-lg font-semibold text-white">AI Generated</div>
                    <div className="text-sm text-gray-400">Plan Type</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-lg font-semibold text-white">{formatDate(currentPlan.created_at)}</div>
                    <div className="text-sm text-gray-400">Plan Date</div>
                  </div>
                  
                  <Button 
                    onClick={() => setShowGenerateModal(true)}
                    variant="outline"
                    className="border-gray-600 text-gray-300 hover:bg-gray-700"
                  >
                    <Calendar className="w-4 h-4 mr-2" />
                    Regenerate Plan
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Week Navigation */}
          <div className="flex items-center justify-between">
            <Button
              onClick={() => navigateWeek('prev')}
              disabled={currentWeekIndex === 0}
              variant="outline"
              className="border-gray-600 text-gray-300 hover:bg-gray-700"
            >
              <ChevronLeft className="w-4 h-4 mr-2" />
              Previous Week
            </Button>
            
            <div className="text-center">
              <h3 className="text-xl font-semibold text-white">Week {currentWeekIndex + 1}</h3>
              <p className="text-gray-400">{getWeekRange()}</p>
            </div>
            
            <Button
              onClick={() => navigateWeek('next')}
              disabled={currentWeekIndex >= (currentPlan.plan_data.weeks.length - 1)}
              variant="outline"
              className="border-gray-600 text-gray-300 hover:bg-gray-700"
            >
              Next Week
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          </div>

          {/* Weekly Calendar */}
          {currentWeek && (
            <div className="grid grid-cols-7 gap-4">
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
                    <h4 className="font-semibold text-white mb-2">Description</h4>
                    <p className="text-gray-300">{selectedWorkout.description}</p>
                  </div>
                  
                  {selectedWorkout.details && (
                    <div>
                      <h4 className="font-semibold text-white mb-2">Details</h4>
                      <p className="text-gray-300">{selectedWorkout.details}</p>
                    </div>
                  )}
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-semibold text-white mb-2">Duration</h4>
                      <p className="text-gray-300">{selectedWorkout.duration_minutes} minutes</p>
                    </div>
                    
                    {selectedWorkout.ftp_percentage_min && selectedWorkout.ftp_percentage_max && (
                      <div>
                        <h4 className="font-semibold text-white mb-2">FTP Range</h4>
                        <p className="text-gray-300">{selectedWorkout.ftp_percentage_min}% - {selectedWorkout.ftp_percentage_max}%</p>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <Button
                      onClick={() => {
                        // Mark workout as complete
                        if (currentPlan) {
                          trainingService.markWorkoutComplete(currentPlan.id, selectedWorkout.id, !selectedWorkout.completed);
                          // Update local state
                          setSelectedWorkout({ ...selectedWorkout, completed: !selectedWorkout.completed });
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
              <CardTitle className="text-white">Training Zones & Activities</CardTitle>
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
                  <span className="text-gray-300">Cross Training: Strength/Other</span>
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
              <CardTitle className="text-white">Generate Training Plan</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Training Goal</label>
                <select
                  value={generateForm.goal}
                  onChange={(e) => setGenerateForm(prev => ({ ...prev, goal: e.target.value }))}
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
                <label className="block text-sm font-medium text-gray-300 mb-2">Weekly Hours</label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={generateForm.weekly_hours}
                  onChange={(e) => setGenerateForm(prev => ({ ...prev, weekly_hours: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-reroute-primary"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Fitness Level</label>
                <select
                  value={generateForm.fitness_level}
                  onChange={(e) => setGenerateForm(prev => ({ ...prev, fitness_level: e.target.value }))}
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
    </div>
  );
};

export default Training; 