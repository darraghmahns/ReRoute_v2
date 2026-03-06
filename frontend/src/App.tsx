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

// Lazy load password reset component
const PasswordResetPageComponent = React.lazy(() =>
  import('./components/PasswordResetForm').then((module) => ({
    default: module.PasswordResetForm,
  }))
);

// Component to handle root route with potential Strava callback
const RootHandler: React.FC = () => {
  const urlParams = new URLSearchParams(window.location.search);
  const hasStravaCallback = urlParams.get('code') && urlParams.get('scope');

  if (hasStravaCallback) {
    return <StravaCallbackPage />;
  }

  return (
    <ProtectedRoute>
      <MainPage />
    </ProtectedRoute>
  );
};

function App() {
  return (
    <Router
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true
      }}
    >
      <div className="min-h-screen flex flex-col bg-reroute-gradient bg-cover">
        <Navigation />
        <main className="container mx-auto px-2 sm:px-4 py-2 sm:py-4 flex-1">
          <React.Suspense
            fallback={
              <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-reroute-primary mx-auto mb-4"></div>
                  <p className="text-white">Loading...</p>
                </div>
              </div>
            }
          >
            <Routes>
              {/* Public routes */}
              <Route path="/auth" element={<AuthPage />} />
              <Route
                path="/reset-password"
                element={<PasswordResetPageComponent />}
              />
              <Route path="/strava-callback" element={<StravaCallbackPage />} />

              {/* Root route with Strava callback detection */}
              <Route path="/" element={<RootHandler />} />
              <Route path="/routes" element={<RootHandler />} />
              <Route path="/training" element={<RootHandler />} />
              <Route path="/dashboard" element={<RootHandler />} />
              <Route
                path="/profile"
                element={
                  <ProtectedRoute>
                    <ProfilePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/profile/subscription"
                element={
                  <ProtectedRoute>
                    <ProfilePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/profile/settings"
                element={
                  <ProtectedRoute>
                    <ProfilePage />
                  </ProtectedRoute>
                }
              />

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
