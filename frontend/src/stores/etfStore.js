import { create } from 'zustand';
import { API_BASE } from '../config';

const useEtfStore = create((set, get) => ({
  snapshot: null,
  status: 'idle',        // 'idle' | 'loading' | 'refreshing' | 'error'
  progress: { done: 0, total: 0, current: '' },
  customSymbols: [],

  setSnapshot: (snapshot) => set({ snapshot, status: 'idle' }),
  setProgress: (progress) => set({ progress }),
  setStatus: (status) => set({ status }),
  setCustomSymbols: (customSymbols) => set({ customSymbols }),

  fetchSnapshot: async () => {
    set({ status: 'loading' });
    try {
      const res = await fetch(`${API_BASE}/api/etf/snapshot`, { credentials: 'include' });
      if (!res.ok) throw new Error('Failed to fetch snapshot');
      const data = await res.json();
      set({ snapshot: data, status: 'idle' });
    } catch (err) {
      console.error('ETF snapshot error:', err);
      set({ status: 'error' });
    }
  },

  fetchCustomSymbols: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/etf/custom`, { credentials: 'include' });
      if (!res.ok) return;
      const data = await res.json();
      set({ customSymbols: data });
    } catch (err) {
      console.error('ETF custom symbols error:', err);
    }
  },

  addCustomSymbol: async (symbol) => {
    const res = await fetch(`${API_BASE}/api/etf/custom/${symbol.toUpperCase()}`, {
      method: 'POST',
      credentials: 'include',
    });
    if (res.ok) {
      await get().fetchCustomSymbols();
    }
    return res.ok;
  },

  removeCustomSymbol: async (symbol) => {
    const res = await fetch(`${API_BASE}/api/etf/custom/${symbol.toUpperCase()}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    if (res.ok) {
      await get().fetchCustomSymbols();
    }
    return res.ok;
  },

  startRefresh: async () => {
    set({ status: 'refreshing', progress: { done: 0, total: 0, current: '' } });
    try {
      const res = await fetch(`${API_BASE}/api/etf/refresh`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Refresh failed');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split('\n').filter((l) => l.startsWith('data: '));
        for (const line of lines) {
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === 'progress' || event.type === 'error') {
              set({ progress: { done: event.done, total: event.total, current: event.symbol } });
            } else if (event.type === 'complete') {
              await get().fetchSnapshot();
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch (err) {
      console.error('ETF refresh error:', err);
      set({ status: 'error' });
    }
  },
}));

export default useEtfStore;
