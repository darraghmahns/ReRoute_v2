import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Button } from './ui/Button';

const Navigation: React.FC = () => {
  const { user, logout, loading } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <nav className="bg-reroute-card border-b border-reroute-card shadow-card">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold text-reroute-primary">Reroute</Link>
        
        {!loading && user && (
          <div className="flex items-center gap-4">
            <Link to="/" className="text-white hover:text-reroute-primary transition-colors">Dashboard</Link>
            <Link to="/routes" className="text-white hover:text-reroute-primary transition-colors">Routes</Link>
            <Link to="/training" className="text-white hover:text-reroute-primary transition-colors">Training</Link>
            <Link to="/profile" className="text-white hover:text-reroute-primary transition-colors">Profile</Link>
            <Link to="/settings" className="text-white hover:text-reroute-primary transition-colors">Settings</Link>
            <Link to="/subscription" className="text-white hover:text-reroute-primary transition-colors">Subscription</Link>
            
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-400">
                Welcome, {user.full_name || user.email}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                className="border-reroute-gray text-white hover:bg-reroute-card"
              >
                Logout
              </Button>
            </div>
          </div>
        )}
        
        {!loading && !user && (
          <div className="flex items-center gap-4">
            <Link to="/auth">
              <Button variant="outline" size="sm" className="border-reroute-gray text-white hover:bg-reroute-card">
                Login
              </Button>
            </Link>
          </div>
        )}
        
        {loading && (
          <span className="text-gray-400">Loading...</span>
        )}
      </div>
    </nav>
  );
};

export default Navigation; 