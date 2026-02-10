import { useState, useEffect, useCallback, useRef } from 'react';
import { Button } from './ui/button';

const HEALTH_URL = 'http://localhost:6900/health';
const POLL_INTERVAL = 1000;
const TIMEOUT_MS = 60000;

export default function StartupScreen({ onReady }) {
  const [status, setStatus] = useState('connecting'); // 'connecting' | 'ready' | 'error'
  const [fadeOut, setFadeOut] = useState(false);
  const readyFired = useRef(false);

  const markReady = useCallback(() => {
    if (readyFired.current) return;
    readyFired.current = true;
    setStatus('ready');
    setFadeOut(true);
    setTimeout(() => onReady(), 400);
  }, [onReady]);

  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch(HEALTH_URL);
      const data = await res.json();
      if (data.status === 'healthy') {
        return true;
      }
    } catch {
      // Backend not ready yet
    }
    return false;
  }, []);

  const startPolling = useCallback(() => {
    setStatus('connecting');
    setFadeOut(false);
    readyFired.current = false;

    const startTime = Date.now();
    const interval = setInterval(async () => {
      const healthy = await checkHealth();
      if (healthy) {
        clearInterval(interval);
        markReady();
        return;
      }
      if (Date.now() - startTime > TIMEOUT_MS) {
        clearInterval(interval);
        setStatus('error');
      }
    }, POLL_INTERVAL);

    return () => clearInterval(interval);
  }, [checkHealth, markReady]);

  // Listen for Tauri backend-ready event (fires when sidecar emits NIRVANA_BACKEND_READY)
  useEffect(() => {
    let unlisten;
    (async () => {
      try {
        const { listen } = await import('@tauri-apps/api/event');
        unlisten = await listen('backend-ready', () => {
          markReady();
        });
      } catch {
        // Not running inside Tauri (e.g. plain browser dev), ignore
      }
    })();
    return () => { if (unlisten) unlisten(); };
  }, [markReady]);

  useEffect(() => {
    const cleanup = startPolling();
    return cleanup;
  }, [startPolling]);

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center bg-background transition-opacity duration-300 ${
        fadeOut ? 'opacity-0' : 'opacity-100'
      }`}
    >
      <div className="flex flex-col items-center gap-6">
        {/* App name */}
        <h1 className="text-4xl font-bold tracking-tight text-foreground">
          Nirvana
        </h1>

        {status === 'connecting' && (
          <>
            {/* Spinner */}
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted-foreground border-t-foreground" />
            <p className="text-sm text-muted-foreground">Starting backend...</p>
          </>
        )}

        {status === 'error' && (
          <div className="flex flex-col items-center gap-4">
            <p className="text-sm text-destructive">
              Backend failed to start within 60 seconds.
            </p>
            <Button variant="outline" onClick={startPolling}>
              Retry
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
