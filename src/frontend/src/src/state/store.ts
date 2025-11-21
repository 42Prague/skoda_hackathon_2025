import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type UserRole = 'manager' | 'hrbp' | 'employee';

interface AppState {
  language: 'en' | 'cs';
  setLanguage: (lang: 'en' | 'cs') => void;
  selectedEmployeeId: string | null;
  setSelectedEmployeeId: (id: string | null) => void;
  selectedTeamId: string | null;
  setSelectedTeamId: (id: string | null) => void;
  currentRole: UserRole;
  setCurrentRole: (role: UserRole) => void;
}

export const useAppStore = create<AppState>(
  persist(
    (set) => ({
      language: 'en',
      setLanguage: (lang) => set({ language: lang }),
      selectedEmployeeId: null,
      setSelectedEmployeeId: (id) => set({ selectedEmployeeId: id }),
      selectedTeamId: null,
      setSelectedTeamId: (id) => set({ selectedTeamId: id }),
      currentRole: 'manager',
      setCurrentRole: (role) => set({ currentRole: role }),
    }),
    {
      name: 'skoda-skill-coach-storage',
    }
  )
);

// Separate store export for role (for convenience)
export const useRoleStore = () => {
  const currentRole = useAppStore((state) => state.currentRole);
  const setCurrentRole = useAppStore((state) => state.setCurrentRole);
  return { currentRole, setCurrentRole };
};