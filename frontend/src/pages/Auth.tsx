import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '../components/ui/Card';
import {
  loginSchema,
  registerSchema,
  type LoginFormData,
  type RegisterFormData,
} from '../lib/validations';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

const Auth: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { user, login, register, loading, authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect if already authenticated
  useEffect(() => {
    // Only redirect if user is set, not loading, and there is no error
    if (user && !loading && !error) {
      const from = location.state?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [user, loading, error, navigate, location]);

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
      setSuccess(null);
      setIsSubmitting(true);
      await login(data);
      setSuccess('Login successful! Redirecting...');
      // Do not navigate here; let useEffect handle it after user is set
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsSubmitting(false); // Always reset submitting state
    }
  };

  const onSubmitRegister = async (data: RegisterFormData) => {
    try {
      setError(null);
      setSuccess(null);
      setIsSubmitting(true);
      await register({
        email: data.email,
        password: data.password,
        full_name: data.full_name,
      });
      setSuccess('Account created successfully! Please sign in.');
      // After successful registration, switch to login
      setIsLogin(true);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError(null);
    setSuccess(null);
    setIsSubmitting(false); // Reset submitting state when switching modes
    loginForm.reset();
    registerForm.reset();
  };

  // Show loading if checking authentication (initial page load only)
  if (authLoading) {
    return (
      <div className="min-h-full flex items-center justify-center bg-reroute-gradient">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-reroute-primary mx-auto mb-4"></div>
          <p className="text-white">Loading...</p>
        </div>
      </div>
    );
  }

  // Dont render the form if user is already authenticated
  if (user) {
    return null;
  }

  return (
    <div className="min-h-full flex items-center justify-center py-6 sm:py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-6 sm:space-y-8">
        <div className="text-center">
          <h2 className="text-2xl sm:text-3xl font-bold text-white">Reroute</h2>
          <p className="mt-2 text-sm text-gray-400">
            {isLogin ? 'Sign in to your account' : 'Create your account'}
          </p>
        </div>

        <Card className="bg-reroute-card border-reroute-card">
          <CardHeader className="pb-4 sm:pb-6">
            <CardTitle className="text-white text-lg sm:text-xl">
              {isLogin ? 'Sign In' : 'Sign Up'}
            </CardTitle>
            <CardDescription className="text-gray-400 text-sm">
              {isLogin
                ? 'Enter your credentials to access your account'
                : 'Create a new account to get started'}
            </CardDescription>
          </CardHeader>

          <CardContent className="pt-0 px-4 sm:px-6">
            {error && (
              <div className="mb-3 sm:mb-4 p-2 sm:p-3 bg-red-500/10 border border-red-500/20 rounded-md flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs sm:text-sm text-red-400 break-words">
                  {error}
                </p>
              </div>
            )}

            {success && (
              <div className="mb-3 sm:mb-4 p-2 sm:p-3 bg-green-50 border border-green-50/20 rounded-md flex items-start space-x-2">
                <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                <p className="text-xs sm:text-sm text-green-500 break-words">
                  {success}
                </p>
              </div>
            )}

            {isLogin ? (
              <form
                onSubmit={loginForm.handleSubmit(onSubmitLogin)}
                className="space-y-3 sm:space-y-4"
              >
                <div className="space-y-1 sm:space-y-2">
                  <Label htmlFor="email" className="text-white text-sm">
                    Email
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    {...loginForm.register('email')}
                    className={`${loginForm.formState.errors.email ? 'border-red-500 focus:border-red-500: border-gray-600 focus:border-reroute-primary' : 'border-gray-600 focus:border-reroute-primary'} bg-reroute-card text-white placeholder-gray-400 h-10 sm:h-auto text-sm sm:text-base`}
                    disabled={isSubmitting}
                  />
                  {loginForm.formState.errors.email && (
                    <p className="text-xs sm:text-sm text-red-500 flex items-center space-x-1">
                      <AlertCircle className="w-3 h-3" />
                      <span>{loginForm.formState.errors.email.message}</span>
                    </p>
                  )}
                </div>

                <div className="space-y-1 sm:space-y-2">
                  <Label htmlFor="password" className="text-white text-sm">
                    Password
                  </Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Enter your password"
                    {...loginForm.register('password')}
                    className={`${loginForm.formState.errors.password ? 'border-red-500 focus:border-red-500: border-gray-600 focus:border-reroute-primary' : 'border-gray-600 focus:border-reroute-primary'} bg-reroute-card text-white placeholder-gray-400 h-10 sm:h-auto text-sm sm:text-base`}
                    disabled={isSubmitting}
                  />
                  {loginForm.formState.errors.password && (
                    <p className="text-xs sm:text-sm text-red-500 flex items-center space-x-1">
                      <AlertCircle className="w-3 h-3" />
                      <span>{loginForm.formState.errors.password.message}</span>
                    </p>
                  )}
                </div>

                <Button
                  type="submit"
                  className="w-full bg-reroute-primary hover:bg-reroute-primary/80 text-white disabled:opacity-50 h-10 sm:h-auto text-sm sm:text-base mt-4 sm:mt-6"
                  disabled={isSubmitting || loading}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Signing in...
                    </>
                  ) : (
                    'Sign In'
                  )}
                </Button>
              </form>
            ) : (
              <form
                onSubmit={registerForm.handleSubmit(onSubmitRegister)}
                className="space-y-3 sm:space-y-4"
              >
                <div className="space-y-1 sm:space-y-2">
                  <Label
                    htmlFor="register-email"
                    className="text-white text-sm"
                  >
                    Email
                  </Label>
                  <Input
                    id="register-email"
                    type="email"
                    placeholder="Enter your email"
                    {...registerForm.register('email')}
                    className={`${registerForm.formState.errors.email ? 'border-red-500 focus:border-red-500: border-gray-600 focus:border-reroute-primary' : 'border-gray-600 focus:border-reroute-primary'} bg-reroute-card text-white placeholder-gray-400 h-10 sm:h-auto text-sm sm:text-base`}
                    disabled={isSubmitting}
                  />
                  {registerForm.formState.errors.email && (
                    <p className="text-xs sm:text-sm text-red-500 flex items-center space-x-1">
                      <AlertCircle className="w-3 h-3" />
                      <span>{registerForm.formState.errors.email.message}</span>
                    </p>
                  )}
                </div>

                <div className="space-y-1 sm:space-y-2">
                  <Label htmlFor="full_name" className="text-white text-sm">
                    Full Name (Optional)
                  </Label>
                  <Input
                    id="full_name"
                    type="text"
                    placeholder="Enter your full name"
                    {...registerForm.register('full_name')}
                    className={`${registerForm.formState.errors.full_name ? 'border-red-500 focus:border-red-500: border-gray-600 focus:border-reroute-primary' : 'border-gray-600 focus:border-reroute-primary'} bg-reroute-card text-white placeholder-gray-400 h-10 sm:h-auto text-sm sm:text-base`}
                    disabled={isSubmitting}
                  />
                  {registerForm.formState.errors.full_name && (
                    <p className="text-xs sm:text-sm text-red-500 flex items-center space-x-1">
                      <AlertCircle className="w-3 h-3" />
                      <span>
                        {registerForm.formState.errors.full_name.message}
                      </span>
                    </p>
                  )}
                </div>

                <div className="space-y-1 sm:space-y-2">
                  <Label
                    htmlFor="register-password"
                    className="text-white text-sm"
                  >
                    Password
                  </Label>
                  <Input
                    id="register-password"
                    type="password"
                    placeholder="Enter your password"
                    {...registerForm.register('password')}
                    className={`${registerForm.formState.errors.password ? 'border-red-500 focus:border-red-500: border-gray-600 focus:border-reroute-primary' : 'border-gray-600 focus:border-reroute-primary'} bg-reroute-card text-white placeholder-gray-400 h-10 sm:h-auto text-sm sm:text-base`}
                    disabled={isSubmitting}
                  />
                  {registerForm.formState.errors.password && (
                    <p className="text-xs sm:text-sm text-red-500 flex items-center space-x-1">
                      <AlertCircle className="w-3 h-3" />
                      <span>
                        {registerForm.formState.errors.password.message}
                      </span>
                    </p>
                  )}
                </div>

                <div className="space-y-1 sm:space-y-2">
                  <Label
                    htmlFor="confirm-password"
                    className="text-white text-sm"
                  >
                    Confirm Password
                  </Label>
                  <Input
                    id="confirm-password"
                    type="password"
                    placeholder="Confirm your password"
                    {...registerForm.register('confirmPassword')}
                    className={`${registerForm.formState.errors.confirmPassword ? 'border-red-500 focus:border-red-500: border-gray-600 focus:border-reroute-primary' : 'border-gray-600 focus:border-reroute-primary'} bg-reroute-card text-white placeholder-gray-400 h-10 sm:h-auto text-sm sm:text-base`}
                    disabled={isSubmitting}
                  />
                  {registerForm.formState.errors.confirmPassword && (
                    <p className="text-xs sm:text-sm text-red-500 flex items-center space-x-1">
                      <AlertCircle className="w-3 h-3" />
                      <span>
                        {registerForm.formState.errors.confirmPassword.message}
                      </span>
                    </p>
                  )}
                </div>

                <Button
                  type="submit"
                  className="w-full bg-reroute-primary hover:bg-reroute-primary/80 text-white disabled:opacity-50 h-10 sm:h-auto text-sm sm:text-base mt-4 sm:mt-6"
                  disabled={isSubmitting || loading}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Creating account...
                    </>
                  ) : (
                    'Sign Up'
                  )}
                </Button>
              </form>
            )}
          </CardContent>

          <CardFooter className="pt-3 sm:pt-6 px-4 sm:px-6">
            <Button
              type="button"
              variant="ghost"
              onClick={toggleMode}
              className="w-full text-reroute-primary hover:text-reroute-primary/80 hover:bg-reroute-card h-10 sm:h-auto text-sm sm:text-base"
              disabled={isSubmitting}
            >
              {isLogin
                ? 'Need an account? Sign up'
                : 'Already have an account? Sign in'}
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

export default Auth;
