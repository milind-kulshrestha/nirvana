import { create } from 'zustand';

const useAIContextStore = create((set, get) => ({
  // Attached context chips for the compose bar
  // Each: { id, type: 'watchlist'|'etf'|'stock'|'dataset', label, data }
  attachedContexts: [],

  attachContext: (item) =>
    set((s) => {
      if (s.attachedContexts.some((c) => c.id === item.id)) return s;
      return { attachedContexts: [...s.attachedContexts, item] };
    }),

  detachContext: (id) =>
    set((s) => ({
      attachedContexts: s.attachedContexts.filter((c) => c.id !== id),
    })),

  clearContexts: () => set({ attachedContexts: [] }),

  // Registry of AI-sendable components
  registeredComponents: {},

  // Register a component as AI-sendable
  registerComponent: (id, serializeFn, domRef) =>
    set((s) => ({
      registeredComponents: {
        ...s.registeredComponents,
        [id]: { serialize: serializeFn, ref: domRef },
      },
    })),

  // Unregister a component
  unregisterComponent: (id) =>
    set((s) => {
      const { [id]: _, ...rest } = s.registeredComponents;
      return { registeredComponents: rest };
    }),

  // Capture structured data + visual screenshot for a component
  captureComponent: async (id) => {
    const comp = get().registeredComponents[id];
    if (!comp) return null;

    const structuredData = comp.serialize();
    let screenshot = null;

    if (comp.ref?.current) {
      try {
        const { toPng } = await import('html-to-image');
        screenshot = await toPng(comp.ref.current, {
          quality: 0.8,
          pixelRatio: 1,
        });
      } catch (err) {
        console.warn('Screenshot capture failed:', err);
      }
    }

    return { componentId: id, data: structuredData, screenshot };
  },

  // Capture all registered components (structured data only)
  capturePageContext: async () => {
    const components = get().registeredComponents;
    const results = {};
    for (const [id, comp] of Object.entries(components)) {
      try {
        results[id] = { data: comp.serialize() };
      } catch (err) {
        console.warn(`Failed to serialize ${id}:`, err);
      }
    }
    return results;
  },
}));

export default useAIContextStore;
