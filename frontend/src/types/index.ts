// User and Authentication Types
export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
}

// Profile Types
export interface Profile {
  id: string;
  age?: number;
  gender?: string;
  weight_kg?: number;
  height_cm?: number;
  cycling_experience?: string;
  fitness_level?: string;
  weekly_training_hours?: number;
  primary_goals?: string[];
  injury_history?: string;
  medical_conditions?: string;
  nutrition_preferences?: string;
  equipment_available?: string[];
  preferred_training_days?: string[];
  time_availability?: Record<string, unknown>;
  training_preferences?: Record<string, unknown>;
  current_fitness_assessment?: string;
  profile_completed: boolean;
  strava_user_id?: string;
  strava_access_token?: string;
  strava_refresh_token?: string;
  strava_token_expires_at?: string;
  created_at: string;
  updated_at: string;
}

// Route Types
export interface RoutePoint {
  lat: number;
  lng: number;
  elevation_m: number;
}

export interface Route {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  distance_km: number;
  elevation_gain_m: number;
  difficulty_level: string;
  route_points: RoutePoint[];
  gpx_data?: string;
  start_location?: {
    lat: number;
    lng: number;
  };
  bike_type: 'road' | 'gravel' | 'mountain';
  created_at: string;
}

export interface RouteGenerationParams {
  race_name: string;
  start_location: {
    lat: number;
    lng: number;
    address?: string;
  };
  distance_miles: number;
  bike_type: 'road' | 'gravel' | 'mountain';
  difficulty_preference?: string;
}

// Training Plan Types
export interface Workout {
  id: string;
  title: string;
  description: string;
  duration_minutes: number;
  workout_type: 'recovery' | 'endurance' | 'threshold' | 'vo2max' | 'cross_training' | 'rest';
  ftp_percentage_min?: number;
  ftp_percentage_max?: number;
  details?: string;
  completed: boolean;
}

export interface TrainingWeek {
  week_start_date: string;
  workouts: {
    monday: Workout;
    tuesday: Workout;
    wednesday: Workout;
    thursday: Workout;
    friday: Workout;
    saturday: Workout;
    sunday: Workout;
  };
}

export interface TrainingPlan {
  id: string;
  user_id: string;
  name: string;
  goal: string;
  weekly_hours: number;
  start_date: string;
  end_date?: string;
  is_active: boolean;
  plan_data: {
    weeks: TrainingWeek[];
  };
  created_at: string;
  updated_at: string;
}

export interface GeneratePlanRequest {
  goal: string;
  weekly_hours: number;
  fitness_level?: string;
  preferences?: string[];
}

// Strava Types
export interface StravaActivity {
  id: string;
  user_id: string;
  strava_activity_id: number;
  name: string;
  activity_type: string;
  distance_m: number;
  moving_time_s: number;
  elapsed_time_s: number;
  total_elevation_gain_m: number;
  average_speed_ms: number;
  max_speed_ms: number;
  average_heartrate?: number;
  max_heartrate?: number;
  average_power?: number;
  max_power?: number;
  start_date: string;
  activity_data: Record<string, unknown>;
  created_at: string;
  type?: string;
  calories?: number;
  map?: { summary_polyline?: string };
  // Add more fields as needed
}

export interface StravaZone {
  id: string;
  user_id: string;
  zone_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// Chat Types
export interface ChatMessage {
  id: string;
  user_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

// Analytics Types
export interface PerformanceMetrics {
  normalized_power?: number;
  ftp?: number;
  tss?: number;
  recovery_score?: number;
  training_intensity?: number;
  lthr?: number;
  weekly_hours: number;
  training_frequency: number;
  consistency_score: number;
  longest_ride?: {
    distance: number;
    duration: number;
  };
  days_since_last_activity: number;
}

export interface WeeklyActivity {
  week_start: string;
  total_distance: number;
  total_elevation: number;
  total_time: number;
  activities_count: number;
  average_power?: number;
  average_heartrate?: number;
}

// Subscription Types
export interface SubscriptionStatus {
  id: string;
  user_id: string;
  email: string;
  stripe_customer_id?: string;
  stripe_subscription_id?: string;
  subscription_tier: 'free' | 'premium' | 'pro';
  subscribed: boolean;
  subscription_end?: string;
  created_at: string;
  updated_at: string;
}

export interface UsageStats {
  chat_messages: number;
  routes_generated: number;
  training_plans: number;
  analytics_access: boolean;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Map Types
export interface MapLocation {
  lat: number;
  lng: number;
  address?: string;
}

// Form Types
export interface ProfileFormData {
  age?: number;
  gender?: string;
  weight_lbs?: number;
  height_inches?: number;
  cycling_experience?: string;
  fitness_level?: string;
  weekly_training_hours?: number;
  primary_goals?: string[];
  injury_history?: string;
  medical_conditions?: string;
  nutrition_preferences?: string;
  equipment_available?: string[];
  preferred_training_days?: string[];
  time_availability?: Record<string, unknown>;
  training_preferences?: Record<string, unknown>;
  current_fitness_assessment?: string;
}

// Component Props Types
export interface RouteCardProps {
  route: Route;
  onDelete?: (id: string) => void;
  onDownload?: (route: Route) => void;
}

export interface TrainingPlanCardProps {
  plan: TrainingPlan;
  onActivate?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export interface ActivityCardProps {
  activity: StravaActivity;
}

// Error Types
export interface ApiError {
  detail: string;
  status_code: number;
}

// Loading States
export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}

// Navigation Types
export type TabType = 'ai-assistant' | 'routes' | 'training' | 'performance';

// Subscription Tiers
export const SUBSCRIPTION_TIERS = {
  free: {
    chatMessages: 10,
    routesPerMonth: 3,
    trainingPlans: 1,
    performanceAnalytics: false,
    price: 0
  },
  premium: {
    chatMessages: 100,
    routesPerMonth: 25,
    trainingPlans: 5,
    performanceAnalytics: true,
    price: 9.99
  },
  pro: {
    chatMessages: -1, // unlimited
    routesPerMonth: -1,
    trainingPlans: -1,
    performanceAnalytics: true,
    advancedMetrics: true,
    price: 19.99
  }
} as const;

export type SubscriptionTier = keyof typeof SUBSCRIPTION_TIERS; 