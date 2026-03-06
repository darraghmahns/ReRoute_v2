import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '';

const getAuthHeaders = () => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`,
});

export interface SubscriptionStatus {
  tier: 'free' | 'pro';
  status: string;
  current_period_end?: string;
}

export const getSubscriptionStatus = async (): Promise<SubscriptionStatus> => {
  const response = await axios.get(`${API_URL}/api/subscription/status`, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const createCheckoutSession = async (): Promise<string> => {
  const response = await axios.post(
    `${API_URL}/api/subscription/checkout`,
    {},
    { headers: getAuthHeaders() }
  );
  return response.data.url;
};

export const createPortalSession = async (): Promise<string> => {
  const response = await axios.post(
    `${API_URL}/api/subscription/portal`,
    {},
    { headers: getAuthHeaders() }
  );
  return response.data.url;
};
