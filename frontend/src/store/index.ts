import { create } from 'zustand'

interface AppState {
  darkMode: boolean
  toggleDarkMode: () => void
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  currentSession: string
  setCurrentSession: (id: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  darkMode: false,
  toggleDarkMode: () => set((s) => ({ darkMode: !s.darkMode })),
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  currentSession: '',
  setCurrentSession: (id) => set({ currentSession: id }),
}))
