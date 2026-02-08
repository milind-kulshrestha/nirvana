#!/usr/bin/env bash
# bundle-python.sh
#
# Downloads a standalone Python build and bundles it with the backend
# dependencies into the Tauri resources directory.
#
# This script is called by the GitHub Actions CI workflow during the
# release build. It can also be run locally for testing.
#
# The bundled Python + backend ends up in:
#   frontend/src-tauri/resources/python/
#
# At runtime, lib.rs resolves this path and spawns the backend using
# the bundled interpreter instead of the system Python.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RESOURCES_DIR="$PROJECT_ROOT/frontend/src-tauri/resources"
PYTHON_BUNDLE_DIR="$RESOURCES_DIR/python"
PYTHON_STANDALONE_VERSION="20240814"  # python-build-standalone release tag
PYTHON_VERSION="3.11"

# ---------------------------------------------------------------------------
# Detect platform
# ---------------------------------------------------------------------------
detect_platform() {
  local os arch
  os="$(uname -s)"
  arch="$(uname -m)"

  case "$os" in
    Darwin)
      case "$arch" in
        arm64)  echo "aarch64-apple-darwin" ;;
        x86_64) echo "x86_64-apple-darwin" ;;
        *)      echo "Unsupported macOS architecture: $arch" >&2; exit 1 ;;
      esac
      ;;
    MINGW*|MSYS*|CYGWIN*|Windows_NT)
      echo "x86_64-pc-windows-msvc"
      ;;
    Linux)
      case "$arch" in
        x86_64)  echo "x86_64-unknown-linux-gnu" ;;
        aarch64) echo "aarch64-unknown-linux-gnu" ;;
        *)       echo "Unsupported Linux architecture: $arch" >&2; exit 1 ;;
      esac
      ;;
    *)
      echo "Unsupported OS: $os" >&2
      exit 1
      ;;
  esac
}

PLATFORM="${TARGET_TRIPLE:-$(detect_platform)}"
echo "==> Bundling Python for platform: $PLATFORM"

# ---------------------------------------------------------------------------
# Step 1: Download python-build-standalone
# ---------------------------------------------------------------------------
# TODO: Download the correct python-build-standalone release for $PLATFORM.
#
# python-build-standalone provides self-contained Python distributions:
#   https://github.com/indygreg/python-build-standalone/releases
#
# Example URL pattern:
#   https://github.com/indygreg/python-build-standalone/releases/download/
#     ${PYTHON_STANDALONE_VERSION}/cpython-${PYTHON_VERSION}+${PYTHON_STANDALONE_VERSION}-
#     ${PLATFORM}-install_only.tar.gz
#
# For now, we fall back to the system Python for local development builds.

download_standalone_python() {
  local url="https://github.com/indygreg/python-build-standalone/releases/download/${PYTHON_STANDALONE_VERSION}/cpython-${PYTHON_VERSION}.0+${PYTHON_STANDALONE_VERSION}-${PLATFORM}-install_only.tar.gz"
  local archive="/tmp/python-standalone.tar.gz"

  echo "==> Downloading standalone Python from:"
  echo "    $url"

  if command -v curl &>/dev/null; then
    curl -fSL -o "$archive" "$url"
  elif command -v wget &>/dev/null; then
    wget -q -O "$archive" "$url"
  else
    echo "ERROR: Neither curl nor wget available" >&2
    exit 1
  fi

  echo "==> Extracting to $PYTHON_BUNDLE_DIR"
  mkdir -p "$PYTHON_BUNDLE_DIR"
  tar -xzf "$archive" -C "$PYTHON_BUNDLE_DIR" --strip-components=1
  rm -f "$archive"
}

# ---------------------------------------------------------------------------
# Step 2: Install backend dependencies into the bundled Python
# ---------------------------------------------------------------------------
install_backend_deps() {
  local pip="$PYTHON_BUNDLE_DIR/bin/pip3"
  if [[ "$PLATFORM" == *"windows"* ]]; then
    pip="$PYTHON_BUNDLE_DIR/python.exe -m pip"
  fi

  echo "==> Installing backend dependencies"
  $pip install --no-cache-dir -r "$PROJECT_ROOT/backend/requirements.txt"
}

# ---------------------------------------------------------------------------
# Step 3: Copy backend and python-core source into resources
# ---------------------------------------------------------------------------
copy_backend_source() {
  echo "==> Copying backend source"
  cp -r "$PROJECT_ROOT/backend" "$RESOURCES_DIR/backend"

  if [ -d "$PROJECT_ROOT/python-core" ]; then
    echo "==> Copying python-core"
    cp -r "$PROJECT_ROOT/python-core" "$RESOURCES_DIR/python-core"
  fi

  # Remove unnecessary files to reduce bundle size
  find "$RESOURCES_DIR/backend" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
  find "$RESOURCES_DIR/backend" -type f -name "*.pyc" -delete 2>/dev/null || true
  rm -rf "$RESOURCES_DIR/backend/.pytest_cache" 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  echo "==> Project root: $PROJECT_ROOT"
  echo "==> Resources dir: $RESOURCES_DIR"

  # Clean previous bundle
  rm -rf "$PYTHON_BUNDLE_DIR"
  rm -rf "$RESOURCES_DIR/backend"
  rm -rf "$RESOURCES_DIR/python-core"

  if [ "${CI:-false}" = "true" ]; then
    # In CI: download standalone Python
    download_standalone_python
    install_backend_deps
  else
    # Local dev: skip standalone download, just use system Python
    echo "==> Skipping standalone Python download (not in CI)"
    echo "    Set CI=true to force download"
    mkdir -p "$PYTHON_BUNDLE_DIR"
  fi

  copy_backend_source

  echo "==> Python bundle complete!"
  echo "    Python:  $PYTHON_BUNDLE_DIR"
  echo "    Backend: $RESOURCES_DIR/backend"
  ls -la "$RESOURCES_DIR/"
}

main "$@"
