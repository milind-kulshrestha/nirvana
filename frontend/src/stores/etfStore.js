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
    try {
      const res = await fetch(`${API_BASE}/api/etf/custom/${symbol.toUpperCase()}`, {
        method: 'POST',
        credentials: 'include',
      });
      if (res.ok) await get().fetchCustomSymbols();
      return res.ok;
    } catch (err) {
      console.error('ETF add custom symbol error:', err);
      return false;
    }
  },

  removeCustomSymbol: async (symbol) => {
    try {
      const res = await fetch(`${API_BASE}/api/etf/custom/${symbol.toUpperCase()}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (res.ok) await get().fetchCustomSymbols();
      return res.ok;
    } catch (err) {
      console.error('ETF remove custom symbol error:', err);
      return false;
    }
  },

  startRefresh: async () => {
    set({ status: 'refreshing', progress: { done: 0, total: 0, current: '' } });
    let reader = null;
    try {
      const res = await fetch(`${API_BASE}/api/etf/refresh`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Refresh failed');

      reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        // Keep the last (potentially incomplete) line in the buffer
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === 'progress' || event.type === 'error') {
              set({ progress: { done: event.done, total: event.total, current: event.symbol } });
            } else if (event.type === 'complete') {
              await get().fetchSnapshot();
            }
          } catch {
            // ignore malformed events
          }
        }
      }

      // Flush any remaining bytes in the decoder
      const remaining = decoder.decode();
      if (remaining.startsWith('data: ')) {
        try {
          const event = JSON.parse(remaining.slice(6));
          if (event.type === 'complete') await get().fetchSnapshot();
        } catch { /* ignore */ }
      }
    } catch (err) {
      console.error('ETF refresh error:', err);
      set({ status: 'error' });
    } finally {
      if (reader) {
        try { reader.releaseLock(); } catch { /* ignore */ }
      }
      // Ensure status is never stuck in 'refreshing'
      if (useEtfStore.getState().status === 'refreshing') {
        set({ status: 'idle' });
      }
    }
  },
}));

export default useEtfStore;
