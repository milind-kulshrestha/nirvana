use std::sync::{Arc, Mutex};

use log::{error, info, warn};
use tauri::{Emitter, RunEvent};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

/// Shared handle to the sidecar child process so we can kill it on exit.
type SidecarChild = Arc<Mutex<Option<CommandChild>>>;

/// Resolve the path to `python-core/server.py` relative to the project root.
///
/// During development (`cargo dev` / `npx tauri dev`) the binary lives inside
/// `frontend/src-tauri/target/…`, so we walk up from the executable's directory
/// until we find `python-core/server.py`.  In production builds the script is
/// bundled next to the app resources.
fn resolve_server_script() -> String {
    // First, try relative to the current exe (dev builds).
    if let Ok(exe) = std::env::current_exe() {
        let mut dir = exe.parent().map(|p| p.to_path_buf());
        // Walk up at most 8 levels to find the project root.
        for _ in 0..8 {
            if let Some(ref d) = dir {
                let candidate = d.join("python-core").join("server.py");
                if candidate.exists() {
                    return candidate.to_string_lossy().to_string();
                }
                dir = d.parent().map(|p| p.to_path_buf());
            }
        }
    }

    // Fallback: assume cwd is the project root (e.g. `npx tauri dev`).
    let fallback = std::env::current_dir()
        .map(|d| d.join("python-core").join("server.py"))
        .unwrap_or_else(|_| std::path::PathBuf::from("python-core/server.py"));

    // Walk up from cwd as well, since cwd may be frontend/
    let mut dir = Some(fallback.parent().unwrap_or(std::path::Path::new(".")).to_path_buf());
    for _ in 0..4 {
        if let Some(ref d) = dir {
            let candidate = d.join("python-core").join("server.py");
            if candidate.exists() {
                return candidate.to_string_lossy().to_string();
            }
            dir = d.parent().map(|p| p.to_path_buf());
        }
    }

    fallback.to_string_lossy().to_string()
}

/// Spawn the Python backend sidecar and return the child handle.
///
/// The function watches stdout for the `NIRVANA_BACKEND_READY` sentinel and
/// emits a `backend-ready` event to the frontend when it appears.
fn spawn_backend(app: &tauri::App) -> Option<CommandChild> {
    let server_script = resolve_server_script();
    info!("[sidecar] Launching Python backend: python3 {}", server_script);

    let shell = app.shell();
    let command = shell
        .command("python3")
        .args([&server_script]);

    let (mut rx, child) = match command.spawn() {
        Ok(pair) => pair,
        Err(e) => {
            error!("[sidecar] Failed to spawn Python backend: {}", e);
            return None;
        }
    };

    info!("[sidecar] Python backend spawned (pid: {})", child.pid());

    // Clone the app handle for the async event-reading task.
    let app_handle = app.handle().clone();

    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line_bytes) => {
                    let line = String::from_utf8_lossy(&line_bytes);
                    let trimmed = line.trim();

                    if trimmed == "NIRVANA_BACKEND_READY" {
                        info!("[sidecar] Backend is ready!");
                        let _ = app_handle.emit("backend-ready", true);
                    } else if !trimmed.is_empty() {
                        info!("[sidecar:stdout] {}", trimmed);
                    }
                }
                CommandEvent::Stderr(line_bytes) => {
                    let line = String::from_utf8_lossy(&line_bytes);
                    let trimmed = line.trim();
                    if !trimmed.is_empty() {
                        warn!("[sidecar:stderr] {}", trimmed);
                    }
                }
                CommandEvent::Error(err) => {
                    error!("[sidecar] Process error: {}", err);
                }
                CommandEvent::Terminated(payload) => {
                    let code_str = payload
                        .code
                        .map(|c| c.to_string())
                        .unwrap_or_else(|| "unknown".into());
                    let signal_str = payload
                        .signal
                        .map(|s| s.to_string())
                        .unwrap_or_else(|| "none".into());
                    warn!(
                        "[sidecar] Backend process terminated (code={}, signal={})",
                        code_str, signal_str
                    );
                    let _ = app_handle.emit("backend-terminated", code_str);
                }
                _ => {}
            }
        }
    });

    Some(child)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let sidecar_child: SidecarChild = Arc::new(Mutex::new(None));
    let sidecar_for_exit = sidecar_child.clone();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_updater::init())
        .setup(move |app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            // Spawn the Python backend sidecar.
            let child = spawn_backend(app);
            if let Ok(mut guard) = sidecar_child.lock() {
                *guard = child;
            }

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(move |_app_handle, event| {
            if let RunEvent::Exit = event {
                // Kill the sidecar when the app exits.
                if let Ok(mut guard) = sidecar_for_exit.lock() {
                    if let Some(child) = guard.take() {
                        info!("[sidecar] Shutting down Python backend (pid: {})...", child.pid());
                        match child.kill() {
                            Ok(_) => info!("[sidecar] Backend process killed successfully."),
                            Err(e) => error!("[sidecar] Failed to kill backend: {}", e),
                        }
                    }
                }
            }
        });
}
