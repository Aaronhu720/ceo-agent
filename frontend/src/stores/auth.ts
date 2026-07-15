import { create } from "zustand";
import { api } from "@/lib/api";

interface User {
  id: string;
  name: string;
  email: string;
  organization_id: string;
  avatar_url: string | null;
  language: string;
  timezone: string;
  role_name: string | null;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { name: string; email: string; password: string; organization_name: string }) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email, password) => {
    const data = await api.post<{ access_token: string; refresh_token: string }>("/api/auth/login", {
      email,
      password,
    });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    const user = await api.get<User>("/api/auth/me");
    set({ user, isAuthenticated: true, isLoading: false });
  },

  register: async (formData) => {
    const data = await api.post<{ access_token: string; refresh_token: string }>("/api/auth/register", formData);
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    const user = await api.get<User>("/api/auth/me");
    set({ user, isAuthenticated: true, isLoading: false });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null, isAuthenticated: false });
    window.location.href = "/auth/login";
  },

  loadUser: async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      set({ isLoading: false });
      return;
    }
    try {
      const user = await api.get<User>("/api/auth/me");
      set({ user, isAuthenticated: true, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },
}));
