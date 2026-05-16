import { create } from 'zustand';

export type Toast = { id: string; type: 'success' | 'error' | 'info'; message: string };

type State = {
  loadingCount: number;
  toasts: Toast[];
  startLoading: () => void;
  stopLoading: () => void;
  pushToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
};

export const appStore = create<State>((set) => ({
  loadingCount: 0,
  toasts: [],
  startLoading: () => set((s) => ({ loadingCount: s.loadingCount + 1 })),
  stopLoading: () => set((s) => ({ loadingCount: Math.max(0, s.loadingCount - 1) })),
  pushToast: (toast) =>
    set((s) => ({ toasts: [...s.toasts, { ...toast, id: crypto.randomUUID() }] })),
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }))
}));
