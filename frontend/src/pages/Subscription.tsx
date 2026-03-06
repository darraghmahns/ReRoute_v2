import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Check, Zap } from 'lucide-react';
import {
  getSubscriptionStatus,
  createCheckoutSession,
  createPortalSession,
  type SubscriptionStatus,
} from '../services/subscription';

const FREE_FEATURES = [
  '10 AI chat messages / month',
  '3 route generations / month',
  '1 training plan',
];

const PRO_FEATURES = [
  'Unlimited AI chat messages',
  'Unlimited route generations',
  'Unlimited training plans',
  'Performance analytics',
  'Advanced metrics',
];

const Subscription: React.FC = () => {
  const [status, setStatus] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('subscription') === 'success') {
      setSuccessMessage('Welcome to Pro! Your subscription is now active.');
    }

    getSubscriptionStatus()
      .then(setStatus)
      .catch(() => setError('Failed to load subscription status'))
      .finally(() => setLoading(false));
  }, [location.search]);

  const handleUpgrade = async () => {
    setActionLoading(true);
    setError(null);
    try {
      const url = await createCheckoutSession();
      window.location.href = url;
    } catch {
      setError('Failed to start checkout. Please try again.');
      setActionLoading(false);
    }
  };

  const handleManage = async () => {
    setActionLoading(true);
    setError(null);
    try {
      const url = await createPortalSession();
      window.location.href = url;
    } catch {
      setError('Failed to open billing portal. Please try again.');
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-reroute-primary" />
      </div>
    );
  }

  const isPro = status?.tier === 'pro';

  return (
    <div className="max-w-2xl space-y-6">
      {successMessage && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
          <p className="text-green-400 font-medium">{successMessage}</p>
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Current plan badge */}
      <div className="bg-reroute-card border border-reroute-card rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-sm text-gray-400">Current plan</p>
            <h2 className="text-2xl font-bold text-white capitalize">
              {status?.tier ?? 'Free'}{' '}
              {isPro && <span className="text-reroute-primary">✦</span>}
            </h2>
          </div>
          {isPro && status?.current_period_end && (
            <div className="text-right">
              <p className="text-xs text-gray-400">Next billing date</p>
              <p className="text-sm text-white">
                {new Date(status.current_period_end).toLocaleDateString('en-US', {
                  month: 'long',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </p>
            </div>
          )}
        </div>

        {isPro ? (
          <button
            onClick={handleManage}
            disabled={actionLoading}
            className="w-full py-2 px-4 rounded-lg border border-reroute-gray text-white hover:bg-white/5 transition-colors disabled:opacity-50 text-sm"
          >
            {actionLoading ? 'Opening portal...' : 'Manage Subscription'}
          </button>
        ) : (
          <button
            onClick={handleUpgrade}
            disabled={actionLoading}
            className="w-full py-3 px-4 rounded-lg bg-reroute-primary hover:bg-reroute-primary/80 text-white font-semibold transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Zap className="w-4 h-4" />
            {actionLoading ? 'Redirecting...' : 'Upgrade to Pro — $19.99/mo'}
          </button>
        )}
      </div>

      {/* Plan comparison */}
      {!isPro && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Free */}
          <div className="bg-reroute-card border border-reroute-card rounded-xl p-5">
            <h3 className="text-white font-semibold mb-1">Free</h3>
            <p className="text-2xl font-bold text-white mb-4">$0</p>
            <ul className="space-y-2">
              {FREE_FEATURES.map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm text-gray-400">
                  <Check className="w-4 h-4 text-gray-500 flex-shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
          </div>

          {/* Pro */}
          <div className="bg-reroute-card border border-reroute-primary/40 rounded-xl p-5 relative">
            <div className="absolute -top-3 left-4">
              <span className="bg-reroute-primary text-white text-xs font-semibold px-3 py-1 rounded-full">
                Recommended
              </span>
            </div>
            <h3 className="text-white font-semibold mb-1">Pro</h3>
            <p className="text-2xl font-bold text-white mb-1">$19.99</p>
            <p className="text-xs text-gray-400 mb-4">per month</p>
            <ul className="space-y-2">
              {PRO_FEATURES.map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm text-white">
                  <Check className="w-4 h-4 text-reroute-primary flex-shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default Subscription;
