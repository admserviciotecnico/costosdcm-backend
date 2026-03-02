import { create } from 'zustand';

type UiState = {
  darkMode: boolean;
  setDarkMode: (v: boolean) => void;
};

export const uiStore = create<UiState>((set) => ({
  darkMode: false,
  setDarkMode: (darkMode) => {
    if (typeof document !== 'undefined') document.documentElement.classList.toggle('dark', darkMode);
    set({ darkMode });
  }
}));
