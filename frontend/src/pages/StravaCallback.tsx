import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { handleStravaCallback } from '../services/strava';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

const StravaCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Connecting to Strava...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code');
        const error = searchParams.get('error');

        if (error) {
          setStatus('error');
          setMessage('Strava authorization was cancelled or failed.');
          return;
        }

        if (!code) {
          setStatus('error');
          setMessage('No authorization code received from Strava.');
          return;
        }

        // Handle the callback
        const result = await handleStravaCallback(code);
        setStatus('success');
        setMessage(`Successfully connected to Strava! Welcome, ${result.athlete.firstname}!`);
        
        // Redirect to dashboard after a short delay
        setTimeout(() => {
          navigate('/', { replace: true });
        }, 2000);

      } catch (error) {
        setStatus('error');
        setMessage(error instanceof Error ? error.message : 'Failed to connect to Strava.');
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  const getStatusIcon = () => {
    switch (status) {
      case 'loading':
        return <Loader2 className="w-8 h-8 animate-spin text-reroute-primary" />;
      case 'success':
        return <CheckCircle className="w-8 h-8 text-green-500" />;
      case 'error':
        return <XCircle className="w-8 h-8 text-red-500" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'loading':
        return 'text-reroute-primary';
      case 'success':
        return 'text-green-500';
      case 'error':
        return 'text-red-500';
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-reroute-gradient">
      <Card className="max-w-md w-full mx-4">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            {getStatusIcon()}
          </div>
          <CardTitle className={getStatusColor()}>
            {status === 'loading' && 'Connecting to Strava...'}
            {status === 'success' && 'Strava Connected!'}
            {status === 'error' && 'Connection Failed'}
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center">
          <p className="text-gray-600 mb-6">{message}</p>
          
          {status === 'error' && (
            <div className="space-y-3">
              <Button 
                onClick={() => navigate('/settings')}
                className="w-full"
              >
                Go to Settings
              </Button>
              <Button 
                variant="outline"
                onClick={() => navigate('/')}
                className="w-full"
              >
                Go to Dashboard
              </Button>
            </div>
          )}
          
          {status === 'success' && (
            <div className="text-sm text-gray-500">
              Redirecting to dashboard...
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default StravaCallback; 