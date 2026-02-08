"""
Sidecar wrapper for the Nirvana FastAPI backend.

Launched by Tauri to run the Python backend as a child process.
Binds to 127.0.0.1:6900 (localhost only) in single-user desktop mode.

Usage:
    python python-core/server.py          # from project root
    python server.py                      # from python-core/

Tauri will launch this script and watch stdout for the readiness signal:
    NIRVANA_BACKEND_READY
"""

import os
import signal
import sys

# ---------------------------------------------------------------------------
# 1. Path setup  --  ensure the backend package is importable regardless of
#    the working directory Tauri uses when spawning this process.
# ---------------------------------------------------------------------------
_this_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_this_dir)
_backend_dir = os.path.join(_project_root, "backend")

if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# ---------------------------------------------------------------------------
# 2. Environment defaults  --  set *before* any backend module is imported
#    so that app.config.Settings picks them up.
# ---------------------------------------------------------------------------
os.environ.setdefault("SINGLE_USER_MODE", "true")
os.environ.setdefault(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(os.path.expanduser("~"), ".nirvana", "nirvana.db"),
)
# Allow the Tauri frontend (dev + production) to reach the API.
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173,tauri://localhost,https://tauri.localhost")

# ---------------------------------------------------------------------------
# 3. Configuration
# ---------------------------------------------------------------------------
HOST = "127.0.0.1"
PORT = int(os.environ.get("NIRVANA_PORT", "6900"))


def _handle_signal(signum, _frame):
    """Graceful shutdown on SIGINT / SIGTERM."""
    print(f"\n[nirvana-sidecar] Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Start the uvicorn server."""
    import uvicorn  # imported here so path/env setup is done first

    # Register signal handlers for graceful shutdown from Tauri.
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    print(f"[nirvana-sidecar] Starting backend on {HOST}:{PORT}")
    print(f"[nirvana-sidecar] SINGLE_USER_MODE={os.environ.get('SINGLE_USER_MODE')}")
    print(f"[nirvana-sidecar] DATABASE_URL={os.environ.get('DATABASE_URL')}")

    # Uvicorn config -- run programmatically so we can hook the startup event.
    config = uvicorn.Config(
        "app.main:app",
        host=HOST,
        port=PORT,
        log_level="info",
        # Disable reload in production sidecar; Tauri manages the lifecycle.
        reload=False,
    )
    server = uvicorn.Server(config)

    # Patch the startup handler to emit the readiness signal *after* the
    # ASGI app (and its @on_event("startup") hooks) have finished.
    _original_startup = server.startup

    async def _startup_with_signal(*args, **kwargs):
        await _original_startup(*args, **kwargs)
        # This line is the readiness signal that Tauri watches for on stdout.
        print("NIRVANA_BACKEND_READY", flush=True)

    server.startup = _startup_with_signal

    server.run()


if __name__ == "__main__":
    main()
