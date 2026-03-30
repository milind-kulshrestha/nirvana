import { useEffect } from 'react';

/**
 * Register global keyboard shortcuts.
 * @param {Object} shortcuts - Map of key combos to handlers.
 *   Key format: "mod+k" (mod = Cmd on Mac, Ctrl elsewhere), "shift+mod+a", "escape"
 * @param {boolean} enabled - Whether shortcuts are active (default true)
 */
export default function useKeyboardShortcuts(shortcuts, enabled = true) {
  useEffect(() => {
    if (!enabled) return;

    const handler = (e) => {
      const isMac = navigator.platform.includes('Mac');
      const mod = isMac ? e.metaKey : e.ctrlKey;
      const shift = e.shiftKey;
      const key = e.key.toLowerCase();

      for (const [combo, callback] of Object.entries(shortcuts)) {
        const parts = combo.toLowerCase().split('+');
        const comboKey = parts[parts.length - 1];
        const needsMod = parts.includes('mod');
        const needsShift = parts.includes('shift');

        if (
          key === comboKey &&
          mod === needsMod &&
          shift === needsShift
        ) {
          e.preventDefault();
          callback(e);
          return;
        }
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [shortcuts, enabled]);
}
