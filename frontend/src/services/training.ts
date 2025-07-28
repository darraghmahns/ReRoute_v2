import { getToken } from './auth';
import type { TrainingPlan, GeneratePlanRequest, TrainingWeek } from '../types';

const API_URL = import.meta.env.VITE_API_URL || '';

export const trainingService = {
  async generatePlan(request: GeneratePlanRequest): Promise<TrainingPlan> {
    const token = getToken();
    const response = await fetch(`${API_URL}/training/plans/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error('Failed to generate training plan');
    }

    return response.json();
  },

  async getPlans(): Promise<TrainingPlan[]> {
    const token = getToken();
    const response = await fetch(`${API_URL}/training/plans`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch training plans');
    }

    const data = await response.json();
    return data.plans;
  },

  async getPlan(planId: string): Promise<TrainingPlan> {
    const token = getToken();
    const response = await fetch(`${API_URL}/training/plans/${planId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch training plan');
    }

    return response.json();
  },

  async getWeekPlan(
    planId: string,
    weekStartDate: string
  ): Promise<TrainingWeek> {
    const token = getToken();
    const response = await fetch(
      `${API_URL}/training/plans/${planId}/week/${weekStartDate}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch week plan');
    }

    return response.json();
  },

  async markWorkoutComplete(
    planId: string,
    workoutId: string,
    completed: boolean = true
  ): Promise<void> {
    const token = getToken();
    const response = await fetch(
      `${API_URL}/training/plans/${planId}/workout/${workoutId}/complete?completed=${completed}`,
      {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error('Failed to update workout completion status');
    }
  },

  async deletePlan(planId: string): Promise<void> {
    const token = getToken();
    const response = await fetch(`${API_URL}/training/plans/${planId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to delete training plan');
    }
  },
};
