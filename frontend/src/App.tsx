import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import Footer from './components/Footer';
import ProtectedRoute from './components/ProtectedRoute';
import './App.css';

// Placeholder pages
const MainPage = React.lazy(() => import('./pages/Main'));
const ProfilePage = React.lazy(() => import('./pages/Profile'));
const AuthPage = React.lazy(() => import('./pages/Auth'));
const StravaCallbackPage = React.lazy(() => import('./pages/StravaCallback'));
const NotFoundPage = React.lazy(() => import('./pages/NotFound'));

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-reroute-gradient bg-cover">
        <Navigation />
        <main className="container mx-auto px-2 py-4 flex-1">
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
                  <MainPage />
                </ProtectedRoute>
              } />
              <Route path="/profile" element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              } />
              {/* Note: Settings and Subscription are now managed within the Profile page */}
              
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
