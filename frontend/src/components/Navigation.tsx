import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Button } from './ui/Button';
import { Menu, X } from 'lucide-react';

const Navigation: React.FC = () => {
  const { user, logout, loading } = useAuth();
  const location = useLocation();
  const onProfilePage = location.pathname.startsWith('/profile');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
  };

  return (
    <nav className="bg-reroute-card border-b border-reroute-card shadow-card">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <Link to="/" className="text-xl font-bold text-reroute-primary">
            Reroute
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-4">
            {!loading && user && (
              <>
                {!onProfilePage && (
                  <Link
                    to="/profile"
                    className="text-white hover:text-reroute-primary transition-colors"
                  >
                    Profile
                  </Link>
                )}
                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-400 hidden lg:block">
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
              </>
            )}

            {!loading && !user && (
              <Link to="/auth">
                <Button
                  variant="outline"
                  size="sm"
                  className="border-reroute-gray text-white hover:bg-reroute-card"
                >
                  Login
                </Button>
              </Link>
            )}

            {loading && <span className="text-gray-400">Loading...</span>}
          </div>

          {/* Mobile Menu Button */}
          {!loading && (
            <button
              className="md:hidden text-white p-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          )}
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && !loading && (
          <div className="md:hidden mt-4 pb-4 border-t border-reroute-gray pt-4">
            {user ? (
              <div className="space-y-3">
                <div className="text-sm text-gray-400 pb-2">
                  Welcome, {user.full_name || user.email}
                </div>
                {!onProfilePage && (
                  <Link
                    to="/profile"
                    className="block text-white hover:text-reroute-primary transition-colors py-2"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Profile
                  </Link>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    handleLogout();
                    setMobileMenuOpen(false);
                  }}
                  className="w-full border-reroute-gray text-white hover:bg-reroute-card"
                >
                  Logout
                </Button>
              </div>
            ) : (
              <Link to="/auth" onClick={() => setMobileMenuOpen(false)}>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full border-reroute-gray text-white hover:bg-reroute-card"
                >
                  Login
                </Button>
              </Link>
            )}
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navigation;
