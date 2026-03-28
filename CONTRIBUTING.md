# Contributing

Contributions are welcome! Here's how to get started.

Project policy: target GNOME on Wayland only. Do not add or document X11 session support.

## Getting started (Ubuntu)

Clone the repository and run the one-time setup script:

```bash
git clone --recurse-submodules https://github.com/esatbayhan/ttd-gnome.git
cd gnome-todo
./setup-dev.sh
```

This installs all system packages, the Python toolchain, Flatpak runtimes, and
configures git hooks. Safe to re-run — already-satisfied steps are skipped.

Then do a fast local build to verify everything works:

```bash
./dev-install.sh
```

## Building

### First install / release build

Clone the repository (including the `ttd-core` submodule) and run the combined installer:

```bash
git clone --recurse-submodules https://github.com/esatbayhan/gnome-todo.git
cd gnome-todo
./install.sh
```

This installs the GNOME SDK/runtime if needed, builds the app, installs it as a
user Flatpak, and installs/enables the GNOME Shell extension.

For extension-only updates, use `./install-extension.sh`.
For faster extension iterations without logging out each time, use
`./install-extension.sh --reload`.

### Development build (fast, local)

For day-to-day development use the local meson build instead of Flatpak.
It uses Cargo's incremental compilation, so only changed Rust code is
recompiled on subsequent runs.

Additional prerequisites:

```bash
# Debian/Ubuntu
sudo apt install meson ninja-build
# Fedora
sudo dnf install meson ninja-build
```

Then build and install into the project tree:

```bash
./dev-install.sh
```

Artifacts land in `builddir/_install/` — nothing is written outside the project.
The launcher at `builddir/src/gnome-todo` is picked up automatically by the
screenshot generator and the pre-commit hook.

To wipe and reconfigure from scratch:

```bash
./dev-install.sh --reconfigure
```

## Running tests

Run the full CI check (lint, format, tests) with:

```bash
./devtools/ci.sh
```

Or run pytest directly:

```bash
uv run pytest tests/ -v
```

## Code style

- **Python** — use type hints, follow PEP 8. Format with `ruff`.
- **UI** — static widget trees go in Blueprint `.blp` files under `src/ui/`.
  Dynamic content is handled in Python.
- Keep changes focused. One feature or fix per pull request.

## Submitting changes

1. Fork the repository
2. Create a feature branch (`git checkout -b my-feature`)
3. Make your changes and add tests if applicable
4. Ensure all tests pass
5. Open a pull request with a clear description of what you changed and why
