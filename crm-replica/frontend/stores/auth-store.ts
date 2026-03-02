import { create } from 'zustand';
import { User } from '@/types/domain';

type State = {
  token: string | null;
  user: User | null;
  setToken: (v: string | null) => void;
  setUser: (u: User | null) => void;
  logout: () => void;
};

// Security: token is memory-only (no localStorage/sessionStorage persistence).
export const authStore = create<State>((set) => ({
  token: null,
  user: null,
  setToken: (token) => set({ token }),
  setUser: (user) => set({ user }),
  logout: () => set({ token: null, user: null })
}));
