import axios from 'axios';
import type { AuthResponse, LoginCredentials, RegisterData, User, Profile } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'https://reroute-app-33fih5yanq-uc.a.run.app';

export const login = async (credentials: LoginCredentials): Promise<AuthResponse> => {
  try {
    const form = new FormData();
    form.append('username', credentials.email);
    form.append('password', credentials.password);
    const res = await axios.post(`${API_URL}/auth/login`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    localStorage.setItem('token', res.data.access_token);
    return res.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        throw new Error('Invalid email or password. Please check your credentials and try again.');
      } else if (error.response?.status === 422) {
        throw new Error('Please check your email format and ensure password is at least 6 characters.');
      } else if (error.response?.status === 500) {
        throw new Error('Server error. Please try again later.');
      } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
        throw new Error('Unable to connect to server. Please check your internet connection.');
      } else {
        throw new Error('Login failed. Please try again.');
      }
    }
    throw new Error('An unexpected error occurred. Please try again.');
  }
};

export const register = async (data: RegisterData): Promise<User> => {
  try {
    const res = await axios.post(`${API_URL}/auth/register`, data);
    return res.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 400) {
        const detail = error.response.data?.detail;
        if (typeof detail === 'string') {
          if (detail.includes('email') && detail.includes('already')) {
            throw new Error('An account with this email already exists. Please try logging in instead.');
          } else if (detail.includes('password')) {
            throw new Error('Password does not meet requirements. Please ensure it has at least 6 characters with uppercase, lowercase, and number.');
          } else {
            throw new Error(detail);
          }
        }
        throw new Error('Invalid registration data. Please check your information and try again.');
      } else if (error.response?.status === 422) {
        throw new Error('Please check your email format and ensure password meets requirements.');
      } else if (error.response?.status === 500) {
        throw new Error('Server error. Please try again later.');
      } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
        throw new Error('Unable to connect to server. Please check your internet connection.');
      } else {
        throw new Error('Registration failed. Please try again.');
      }
    }
    throw new Error('An unexpected error occurred. Please try again.');
  }
};

export const logout = async (): Promise<void> => {
  localStorage.removeItem('token');
  // Optionally call backend logout endpoint
  await axios.post(`${API_URL}/auth/logout`);
};

export const getCurrentUser = async (): Promise<User> => {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('No token');
  const res = await axios.get(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
};

export const getCurrentUserWithProfile = async (): Promise<{ user: User; profile: Profile | null }> => {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('No token');
  const res = await axios.get(`${API_URL}/auth/me/with-profile`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
};

export const getToken = (): string | null => localStorage.getItem('token'); 

export const updateUser = async (userData: { full_name?: string; email?: string }): Promise<User> => {
  try {
    const res = await axios.put(`${API_URL}/auth/me`, userData, {
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    return res.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 400) {
        throw new Error('Invalid data provided. Please check your information.');
      } else if (error.response?.status === 401) {
        throw new Error('Unauthorized. Please log in again.');
      } else if (error.response?.status === 500) {
        throw new Error('Server error. Please try again later.');
      } else {
        throw new Error('Update failed. Please try again.');
      }
    }
    throw new Error('An unexpected error occurred. Please try again.');
  }
}; 