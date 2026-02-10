import { create } from 'zustand';
import { API_BASE } from '../config';

const useAuthStore = create((set) => ({
  user: null,
  loading: true,
  error: null,

  // Check if user is authenticated
  checkAuth: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/auth/me`, {
        credentials: 'include',
      });

      if (response.ok) {
        const user = await response.json();
        set({ user, loading: false, error: null });
        return true;
      } else {
        set({ user: null, loading: false, error: null });
        return false;
      }
    } catch (error) {
      set({ user: null, loading: false, error: error.message });
      return false;
    }
  },

  // Register new user
  register: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        credentials: 'include',
      });

      const data = await response.json();

      if (response.ok) {
        // Auto-login after registration
        return await useAuthStore.getState().login(email, password);
      } else {
        set({ loading: false, error: data.detail || 'Registration failed' });
        return false;
      }
    } catch (error) {
      set({ loading: false, error: error.message });
      return false;
    }
  },

  // Login user
  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        credentials: 'include',
      });

      const data = await response.json();

      if (response.ok) {
        set({ user: data, loading: false, error: null });
        return true;
      } else {
        set({ loading: false, error: data.detail || 'Login failed' });
        return false;
      }
    } catch (error) {
      set({ loading: false, error: error.message });
      return false;
    }
  },

  // Logout user
  logout: async () => {
    try {
      await fetch(`${API_BASE}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
      set({ user: null, error: null });
      return true;
    } catch (error) {
      set({ error: error.message });
      return false;
    }
  },

  // Clear error
  clearError: () => set({ error: null }),
}));

export default useAuthStore;
