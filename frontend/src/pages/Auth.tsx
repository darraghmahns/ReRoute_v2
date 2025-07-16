import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/Card';
import { loginSchema, registerSchema, type LoginFormData, type RegisterFormData } from '../lib/validations';

const Auth: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user, login, register, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect if already authenticated
  useEffect(() => {
    if (user && !loading) {
      const from = location.state?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [user, loading, navigate, location]);

  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const registerForm = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
      full_name: '',
    },
  });

  const onSubmitLogin = async (data: LoginFormData) => {
    try {
      setError(null);
      await login(data);
      // Redirect to the page they were trying to access, or dashboard
      const from = location.state?.from?.pathname || '/';
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  const onSubmitRegister = async (data: RegisterFormData) => {
    try {
      setError(null);
      await register({
        email: data.email,
        password: data.password,
        full_name: data.full_name,
      });
      // After successful registration, switch to login
      setIsLogin(true);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError(null);
    loginForm.reset();
    registerForm.reset();
  };

  // Show loading if checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-reroute-gradient">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-reroute-primary mx-auto mb-4"></div>
          <p className="text-white">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render the form if user is already authenticated
  if (user) {
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-white">Reroute</h2>
          <p className="mt-2 text-sm text-gray-400">
            {isLogin ? 'Sign in to your account' : 'Create your account'}
          </p>
        </div>

        <Card className="bg-reroute-card border-reroute-card">
          <CardHeader>
            <CardTitle className="text-white">{isLogin ? 'Sign In' : 'Sign Up'}</CardTitle>
            <CardDescription className="text-gray-400">
              {isLogin 
                ? 'Enter your credentials to access your account'
                : 'Create a new account to get started'
              }
            </CardDescription>
          </CardHeader>

          <CardContent>
            {error && (
              <div className="mb-4 p-3 bg-reroute-red/10 border border-reroute-red/20 rounded-md">
                <p className="text-sm text-reroute-red">{error}</p>
              </div>
            )}

            {isLogin ? (
              <form onSubmit={loginForm.handleSubmit(onSubmitLogin)} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-white">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    {...loginForm.register('email')}
                    className={`${loginForm.formState.errors.email ? 'border-reroute-red' : 'border-reroute-gray'} bg-reroute-card text-white placeholder-gray-400`}
                  />
                  {loginForm.formState.errors.email && (
                    <p className="text-sm text-reroute-red">
                      {loginForm.formState.errors.email.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-white">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Enter your password"
                    {...loginForm.register('password')}
                    className={`${loginForm.formState.errors.password ? 'border-reroute-red' : 'border-reroute-gray'} bg-reroute-card text-white placeholder-gray-400`}
                  />
                  {loginForm.formState.errors.password && (
                    <p className="text-sm text-reroute-red">
                      {loginForm.formState.errors.password.message}
                    </p>
                  )}
                </div>

                <Button
                  type="submit"
                  className="w-full bg-reroute-primary hover:bg-reroute-primary/80 text-white"
                  disabled={loading}
                >
                  {loading ? 'Signing in...' : 'Sign In'}
                </Button>
              </form>
            ) : (
              <form onSubmit={registerForm.handleSubmit(onSubmitRegister)} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="register-email" className="text-white">Email</Label>
                  <Input
                    id="register-email"
                    type="email"
                    placeholder="Enter your email"
                    {...registerForm.register('email')}
                    className={`${registerForm.formState.errors.email ? 'border-reroute-red' : 'border-reroute-gray'} bg-reroute-card text-white placeholder-gray-400`}
                  />
                  {registerForm.formState.errors.email && (
                    <p className="text-sm text-reroute-red">
                      {registerForm.formState.errors.email.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="full_name" className="text-white">Full Name (Optional)</Label>
                  <Input
                    id="full_name"
                    type="text"
                    placeholder="Enter your full name"
                    {...registerForm.register('full_name')}
                    className="border-reroute-gray bg-reroute-card text-white placeholder-gray-400"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="register-password" className="text-white">Password</Label>
                  <Input
                    id="register-password"
                    type="password"
                    placeholder="Enter your password"
                    {...registerForm.register('password')}
                    className={`${registerForm.formState.errors.password ? 'border-reroute-red' : 'border-reroute-gray'} bg-reroute-card text-white placeholder-gray-400`}
                  />
                  {registerForm.formState.errors.password && (
                    <p className="text-sm text-reroute-red">
                      {registerForm.formState.errors.password.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm-password" className="text-white">Confirm Password</Label>
                  <Input
                    id="confirm-password"
                    type="password"
                    placeholder="Confirm your password"
                    {...registerForm.register('confirmPassword')}
                    className={`${registerForm.formState.errors.confirmPassword ? 'border-reroute-red' : 'border-reroute-gray'} bg-reroute-card text-white placeholder-gray-400`}
                  />
                  {registerForm.formState.errors.confirmPassword && (
                    <p className="text-sm text-reroute-red">
                      {registerForm.formState.errors.confirmPassword.message}
                    </p>
                  )}
                </div>

                <Button
                  type="submit"
                  className="w-full bg-reroute-primary hover:bg-reroute-primary/80 text-white"
                  disabled={loading}
                >
                  {loading ? 'Creating account...' : 'Sign Up'}
                </Button>
              </form>
            )}
          </CardContent>

          <CardFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={toggleMode}
              className="w-full text-reroute-primary hover:text-reroute-primary/80 hover:bg-reroute-card"
            >
              {isLogin ? 'Need an account? Sign up' : 'Already have an account? Sign in'}
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

export default Auth; 