import { useEffect, useRef, useCallback } from 'react';
import useAIContextStore from '../stores/aiContextStore';

export function useAISerializable(componentId, serializeFn) {
  const ref = useRef(null);
  const register = useAIContextStore((s) => s.registerComponent);
  const unregister = useAIContextStore((s) => s.unregisterComponent);

  // Memoize the serialize function to avoid re-registration on every render
  const stableSerialize = useCallback(serializeFn, [serializeFn]);

  useEffect(() => {
    register(componentId, stableSerialize, ref);
    return () => unregister(componentId);
  }, [componentId, stableSerialize, register, unregister]);

  return ref;
}
