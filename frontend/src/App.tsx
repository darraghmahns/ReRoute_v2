import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import Footer from './components/Footer';
import ProtectedRoute from './components/ProtectedRoute';
import './App.css';

// Placeholder pages
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const RoutesPage = React.lazy(() => import('./pages/Routes'));
const TrainingPage = React.lazy(() => import('./pages/Training'));
const ProfilePage = React.lazy(() => import('./pages/Profile'));
const AuthPage = React.lazy(() => import('./pages/Auth'));
const SettingsPage = React.lazy(() => import('./pages/Settings'));
const StravaCallbackPage = React.lazy(() => import('./pages/StravaCallback'));
const SubscriptionPage = React.lazy(() => import('./pages/Subscription'));
const NotFoundPage = React.lazy(() => import('./pages/NotFound'));

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-reroute-gradient bg-cover">
        <Navigation />
        <main className="flex-1 container mx-auto px-2 py-4">
          <React.Suspense fallback={
            <div className="min-h-screen flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-reroute-primary mx-auto mb-4"></div>
                <p className="text-white">Loading...</p>
              </div>
            </div>
          }>
            <Routes>
              {/* Public routes */}
              <Route path="/auth" element={<AuthPage />} />
              <Route path="/strava-callback" element={<StravaCallbackPage />} />
              
              {/* Protected routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } />
              <Route path="/routes" element={
                <ProtectedRoute>
                  <RoutesPage />
                </ProtectedRoute>
              } />
              <Route path="/training" element={
                <ProtectedRoute>
                  <TrainingPage />
                </ProtectedRoute>
              } />
              <Route path="/profile" element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              } />
              <Route path="/settings/*" element={
                <ProtectedRoute>
                  <SettingsPage />
                </ProtectedRoute>
              } />
              <Route path="/subscription" element={
                <ProtectedRoute>
                  <SubscriptionPage />
                </ProtectedRoute>
              } />
              
              {/* 404 route */}
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </React.Suspense>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;
