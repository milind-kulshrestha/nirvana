import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('etfStore', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('initial state is idle with no snapshot', async () => {
    const { default: useEtfStore } = await import('./etfStore');
    const state = useEtfStore.getState();
    expect(state.snapshot).toBeNull();
    expect(state.status).toBe('idle');
    expect(state.customSymbols).toEqual([]);
  });

  it('setSnapshot updates snapshot', async () => {
    const { default: useEtfStore } = await import('./etfStore');
    const fake = { built_at: '2026-03-16T20:00:00Z', groups: {}, column_ranges: {} };
    useEtfStore.getState().setSnapshot(fake);
    expect(useEtfStore.getState().snapshot).toEqual(fake);
    expect(useEtfStore.getState().status).toBe('idle');
  });

  it('setProgress updates progress fields', async () => {
    const { default: useEtfStore } = await import('./etfStore');
    useEtfStore.getState().setProgress({ done: 5, total: 180, current: 'SPY' });
    const { progress } = useEtfStore.getState();
    expect(progress.done).toBe(5);
    expect(progress.current).toBe('SPY');
  });
});
