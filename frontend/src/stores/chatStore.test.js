import { describe, it, expect, beforeEach, vi } from 'vitest';

// Minimal localStorage mock
const store = {};
const localStorageMock = {
  getItem: (k) => store[k] ?? null,
  setItem: (k, v) => { store[k] = String(v); },
  removeItem: (k) => { delete store[k]; },
};
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock, writable: true });

describe('chatStore model selection', () => {
  beforeEach(() => {
    Object.keys(store).forEach((k) => delete store[k]);
    vi.resetModules();
  });

  it('has selectedModel in initial state', async () => {
    const { default: useChatStore } = await import('./chatStore');
    expect(useChatStore.getState().selectedModel).toBeDefined();
  });

  it('setSelectedModel updates state and persists to localStorage', async () => {
    const { default: useChatStore } = await import('./chatStore');
    useChatStore.getState().setSelectedModel('gpt-4o');
    expect(useChatStore.getState().selectedModel).toBe('gpt-4o');
    expect(localStorage.getItem('nirvana_selected_model')).toBe('gpt-4o');
  });
});
