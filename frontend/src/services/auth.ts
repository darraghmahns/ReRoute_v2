import axios from 'axios';
import type { AuthResponse, LoginCredentials, RegisterData, User, Profile } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002';

export const login = async (credentials: LoginCredentials): Promise<AuthResponse> => {
  const form = new FormData();
  form.append('username', credentials.email);
  form.append('password', credentials.password);
  const res = await axios.post(`${API_URL}/auth/login`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  localStorage.setItem('token', res.data.access_token);
  return res.data;
};

export const register = async (data: RegisterData): Promise<User> => {
  const res = await axios.post(`${API_URL}/auth/register`, data);
  return res.data;
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