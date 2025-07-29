import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Label } from './ui/Label';
import Modal from './ui/Modal';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

const changePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, 'Current password is required'),
    newPassword: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

interface ChangePasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ChangePasswordModal: React.FC<ChangePasswordModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const form = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    },
  });

  const onSubmit = async (data: ChangePasswordFormData) => {
    try {
      setError(null);
      setSuccess(null);
      setIsSubmitting(true);

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('You must be logged in to change your password');
      }

      const response = await fetch('/api/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: data.currentPassword,
          new_password: data.newPassword,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Password change failed');
      }

      const result = await response.json();
      setSuccess(result.message);
      form.reset();

      // Close modal after successful change
      setTimeout(() => {
        handleClose();
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    form.reset();
    setError(null);
    setSuccess(null);
    setIsSubmitting(false);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Change Password">
      <div className="space-y-4">
        <p className="text-gray-400 text-sm">
          Update your account password. Make sure to use a strong password.
        </p>

        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-md flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {success && (
          <div className="p-3 bg-green-50 border border-green-50/20 rounded-md flex items-start space-x-2">
            <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-green-500">{success}</p>
          </div>
        )}

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="currentPassword" className="text-white">
              Current Password
            </Label>
            <Input
              id="currentPassword"
              type="password"
              placeholder="Enter current password"
              {...form.register('currentPassword')}
              className={`${
                form.formState.errors.currentPassword
                  ? 'border-red-500 focus:border-red-500'
                  : 'border-gray-600 focus:border-reroute-primary'
              } bg-reroute-card text-white placeholder-gray-400`}
              disabled={isSubmitting}
            />
            {form.formState.errors.currentPassword && (
              <p className="text-sm text-red-500 flex items-center space-x-1">
                <AlertCircle className="w-3 h-3" />
                <span>{form.formState.errors.currentPassword.message}</span>
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="newPassword" className="text-white">
              New Password
            </Label>
            <Input
              id="newPassword"
              type="password"
              placeholder="Enter new password"
              {...form.register('newPassword')}
              className={`${
                form.formState.errors.newPassword
                  ? 'border-red-500 focus:border-red-500'
                  : 'border-gray-600 focus:border-reroute-primary'
              } bg-reroute-card text-white placeholder-gray-400`}
              disabled={isSubmitting}
            />
            {form.formState.errors.newPassword && (
              <p className="text-sm text-red-500 flex items-center space-x-1">
                <AlertCircle className="w-3 h-3" />
                <span>{form.formState.errors.newPassword.message}</span>
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword" className="text-white">
              Confirm New Password
            </Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="Confirm new password"
              {...form.register('confirmPassword')}
              className={`${
                form.formState.errors.confirmPassword
                  ? 'border-red-500 focus:border-red-500'
                  : 'border-gray-600 focus:border-reroute-primary'
              } bg-reroute-card text-white placeholder-gray-400`}
              disabled={isSubmitting}
            />
            {form.formState.errors.confirmPassword && (
              <p className="text-sm text-red-500 flex items-center space-x-1">
                <AlertCircle className="w-3 h-3" />
                <span>{form.formState.errors.confirmPassword.message}</span>
              </p>
            )}
          </div>

          <div className="flex space-x-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              className="flex-1 border-gray-600 text-gray-300 hover:bg-gray-700"
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="flex-1 bg-reroute-primary hover:bg-reroute-primary/80 text-white"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : (
                'Update Password'
              )}
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
};
