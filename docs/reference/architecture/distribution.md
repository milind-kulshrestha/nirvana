# Distribution & Auto-Updates

How Nirvana desktop builds are created, signed, and distributed.

## Build Pipeline

Releases are built via GitHub Actions (`.github/workflows/release.yml`). The workflow triggers on version tags (`v*`).

### Build Matrix

| Platform | Target | Output |
|----------|--------|--------|
| macOS | `universal-apple-darwin` | `.dmg`, `.app` |
| Windows | `x86_64-pc-windows-msvc` | `.msi`, `.exe` |

### Build Steps

1. Checkout code
2. Set up Node.js 20, Rust stable, Python 3.11
3. Run `scripts/bundle-python.sh` to package a standalone Python interpreter with backend dependencies into `frontend/src-tauri/resources/`
4. Install frontend deps and build (`npm ci && npm run build`)
5. `tauri-apps/tauri-action` builds the Tauri app, signs it, and uploads artifacts to a draft GitHub Release

### Python Bundling

The app ships with a self-contained Python runtime (via [python-build-standalone](https://github.com/indygreg/python-build-standalone)) so users do not need Python installed. The `scripts/bundle-python.sh` script:

- Downloads the correct python-build-standalone for the target platform
- Installs `backend/requirements.txt` into the bundled Python
- Copies `backend/` and `python-core/` into Tauri resources
- Strips `__pycache__` and `.pyc` files to reduce bundle size

## Auto-Updates

Nirvana uses `tauri-plugin-updater` to check for and install updates.

### How It Works

1. On launch, the app checks the update endpoint for a `latest.json` file
2. The endpoint points to the latest GitHub Release assets
3. If a newer version exists, the update signature is verified against the embedded public key
4. The user is prompted to download and install the update

### Configuration

Update settings are in `frontend/src-tauri/tauri.conf.json` under `plugins.updater`:

- `pubkey` -- Ed25519 public key used to verify update signatures
- `endpoints` -- URLs to check for `latest.json`

The corresponding private key (`TAURI_SIGNING_PRIVATE_KEY`) is stored as a GitHub Actions secret.

### Generating Signing Keys

```bash
npx @tauri-apps/cli signer generate -w ~/.tauri/nirvana.key
```

This outputs a public key (paste into `tauri.conf.json`) and a private key (add as `TAURI_SIGNING_PRIVATE_KEY` secret).

## Creating a Release

```bash
# 1. Bump version in frontend/src-tauri/tauri.conf.json
# 2. Commit and tag
git tag v0.2.0
git push origin v0.2.0

# 3. GitHub Actions builds all platforms and creates a draft release
# 4. Review the draft release on GitHub, edit notes, then publish
```

## Code Signing

### macOS (Apple Developer ID)

- Requires an Apple Developer Program membership ($99/year)
- Certificate: "Developer ID Application" exported as `.p12`
- Notarization: Apple ID + app-specific password
- Secrets needed: `APPLE_CERTIFICATE`, `APPLE_CERTIFICATE_PASSWORD`, `APPLE_SIGNING_IDENTITY`, `APPLE_ID`, `APPLE_PASSWORD`, `APPLE_TEAM_ID`

Without code signing, macOS users will see Gatekeeper warnings and must right-click to open.

### Windows (Authenticode)

- Requires an EV or OV code signing certificate (~$200-400/year)
- Providers: DigiCert, Sectigo, SSL.com
- Without signing, Windows SmartScreen will warn users

### Update Signing (Required)

Tauri update signatures use Ed25519 keys (not related to OS code signing). These are required for the auto-updater to work:

- `TAURI_SIGNING_PRIVATE_KEY` -- base64-encoded private key
- `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` -- passphrase for the key
