import { create } from 'zustand';

const useLayoutStore = create((set) => ({
  // Left sidebar
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  collapseSidebar: () => set({ sidebarCollapsed: true }),
  expandSidebar: () => set({ sidebarCollapsed: false }),

  // Right rail
  rightRailOpen: false,
  rightRailTab: 'steps', // 'steps' | 'sources' | 'skills'
  toggleRightRail: () => set((s) => ({ rightRailOpen: !s.rightRailOpen })),
  openRightRail: (tab) => set({ rightRailOpen: true, ...(tab ? { rightRailTab: tab } : {}) }),
  closeRightRail: () => set({ rightRailOpen: false }),
  setRightRailTab: (tab) => set({ rightRailTab: tab }),
}));

export default useLayoutStore;
