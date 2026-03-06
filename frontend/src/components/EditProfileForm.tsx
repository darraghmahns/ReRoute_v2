import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Label } from './ui/Label';
import { updateUser } from '../services/auth';
import { updateProfile } from '../services/profile';
import type { User, Profile } from '../types';
import { Camera, User as UserIcon, MapPin } from 'lucide-react';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string;

interface GeocodingSuggestion {
  place_name: string;
  center: [number, number]; // [lng, lat]
}

interface EditProfileFormProps {
  user: User | null;
  profile?: Profile | null;
  onSave: (updatedUser: User) => void;
  onCancel: () => void;
}

const EditProfileForm: React.FC<EditProfileFormProps> = ({
  user,
  profile,
  onSave,
  onCancel,
}) => {
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
  });

  // Address state
  const [addressQuery, setAddressQuery] = useState(profile?.home_address_label || '');
  const [suggestions, setSuggestions] = useState<GeocodingSuggestion[]>([]);
  const [selectedAddress, setSelectedAddress] = useState<{
    lat: number;
    lng: number;
    label: string;
  } | null>(
    profile?.home_lat && profile?.home_lng && profile?.home_address_label
      ? { lat: profile.home_lat, lng: profile.home_lng, label: profile.home_address_label }
      : null
  );
  const [showSuggestions, setShowSuggestions] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch suggestions from Mapbox Geocoding API
  useEffect(() => {
    const query = addressQuery.trim();

    // If the query matches the currently selected address, don't re-fetch
    if (selectedAddress && query === selectedAddress.label) {
      setSuggestions([]);
      return;
    }

    if (!query || query.length < 3 || !MAPBOX_TOKEN) {
      setSuggestions([]);
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      try {
        const encoded = encodeURIComponent(query);
        const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encoded}.json?access_token=${MAPBOX_TOKEN}&types=place,address&limit=5`;
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        setSuggestions(data.features || []);
        setShowSuggestions(true);
      } catch {
        // Silently ignore geocoding errors — the field is optional
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [addressQuery, selectedAddress]);

  const handleSuggestionSelect = (suggestion: GeocodingSuggestion) => {
    const [lng, lat] = suggestion.center;
    setSelectedAddress({ lat, lng, label: suggestion.place_name });
    setAddressQuery(suggestion.place_name);
    setSuggestions([]);
    setShowSuggestions(false);
  };

  const handleAddressChange = (value: string) => {
    setAddressQuery(value);
    // If user edits the field after selecting, clear the selection
    if (selectedAddress && value !== selectedAddress.label) {
      setSelectedAddress(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const updatedUser = await updateUser(formData);

      // Only update profile if address was selected (has lat/lng)
      if (selectedAddress) {
        await updateProfile({
          home_lat: selectedAddress.lat,
          home_lng: selectedAddress.lng,
          home_address_label: selectedAddress.label,
        });
      }

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
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
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
        <p className="text-sm text-gray-400">Profile photo upload coming soon</p>
      </div>

      {/* Name + Email */}
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

      {/* Home Location */}
      <div>
        <Label htmlFor="home_address" className="text-white flex items-center gap-1">
          <MapPin className="w-4 h-4" />
          Home Location
        </Label>
        {!MAPBOX_TOKEN ? (
          <p className="text-xs text-gray-500 mt-1">
            Address search unavailable — map token not configured
          </p>
        ) : (
          <>
            <p className="text-xs text-gray-400 mb-1">
              Used by the AI for generating routes from your home
            </p>
            <div className="relative">
              <Input
                id="home_address"
                type="text"
                value={addressQuery}
                onChange={(e) => handleAddressChange(e.target.value)}
                onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                placeholder="Search for your city or address..."
                className="mt-1 bg-white text-black placeholder-gray-500"
                autoComplete="off"
              />
              {showSuggestions && suggestions.length > 0 && (
                <ul className="absolute z-50 left-0 right-0 mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-lg overflow-hidden">
                  {suggestions.map((s, i) => (
                    <li key={s.place_name || i}>
                      <button
                        type="button"
                        className="w-full text-left px-3 py-2 text-sm text-white hover:bg-gray-700 flex items-center gap-2"
                        onMouseDown={() => handleSuggestionSelect(s)}
                      >
                        <MapPin className="w-3 h-3 text-gray-400 flex-shrink-0" />
                        <span className="truncate">{s.place_name}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            {selectedAddress && (
              <p className="text-xs text-green-400 mt-1 flex items-center gap-1">
                ✓ {selectedAddress.label}
              </p>
            )}
          </>
        )}
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
