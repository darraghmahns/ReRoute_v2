import React, { useState } from 'react';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Label } from './ui/Label';
import { updateUser } from '../services/auth';
import type { User } from '../types';
import { Camera, User as UserIcon } from 'lucide-react';

interface EditProfileFormProps {
  user: User | null;
  onSave: (updatedUser: User) => void;
  onCancel: () => void;
}

const EditProfileForm: React.FC<EditProfileFormProps> = ({
  user,
  onSave,
  onCancel,
}) => {
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const updatedUser = await updateUser(formData);
      onSave(updatedUser);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="bg-red-500 border border-red-500/20 rounded-lg p-3">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Profile Photo Section */}
      <div className="flex flex-col items-center space-y-4">
        <div className="relative">
          <div className="w-24 h-24 bg-gradient-to-br from-reroute-primary to-reroute-purple rounded-full flex items-center justify-center">
            <UserIcon className="w-12 h-12 text-white" />
          </div>
          <button
            type="button"
            className="absolute -bottom-1 -right-1 p-2 route-card rounded-full shadow-card hover:shadow-lg transition-shadow border border-reroute-gray"
          >
            <Camera className="w-4 h-4 text-gray-400" />
          </button>
        </div>
        <p className="text-sm text-gray-400">
          Profile photo upload coming soon
        </p>
      </div>

      {/* Name Fields */}
      <div className="space-y-4">
        <div>
          <Label htmlFor="full_name" className="text-white">
            Full Name
          </Label>
          <Input
            id="full_name"
            type="text"
            value={formData.full_name}
            onChange={(e) => handleChange('full_name', e.target.value)}
            placeholder="Enter your full name"
            className="mt-1 bg-white text-black placeholder-gray-500"
          />
        </div>
        <div>
          <Label htmlFor="email" className="text-white">
            Email Address
          </Label>
          <Input
            id="email"
            type="email"
            value={formData.email}
            onChange={(e) => handleChange('email', e.target.value)}
            placeholder="Enter your email address"
            className="mt-1 bg-white text-black placeholder-gray-500"
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-3">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          className="flex-1 border-reroute-gray text-white hover:bg-reroute-card"
          disabled={loading}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          className="flex-1 bg-reroute-primary hover:bg-reroute-primary/80 text-white"
          disabled={loading}
        >
          {loading ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>
    </form>
  );
};

export default EditProfileForm;
