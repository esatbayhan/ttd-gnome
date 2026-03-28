#!/usr/bin/env bash
# Fast local development build — no Flatpak sandbox, incremental Cargo builds.
# Artifacts are installed inside builddir/_install/ and nothing is written
# outside the project tree.
#
# Requires: meson, ninja  (and cargo for the Rust core)
#   Debian/Ubuntu: sudo apt install meson ninja-build
#   Fedora:        sudo dnf install meson ninja-build
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILDDIR="$SCRIPT_DIR/builddir"
INSTALLDIR="$BUILDDIR/_install"
RECONFIGURE=0

usage() {
    cat <<EOF
Usage: $0 [--reconfigure]

Builds the app locally with meson/ninja for a fast development workflow.
Artifacts are installed to builddir/_install/ — nothing written outside the
project tree.  Cargo uses its own incremental cache so only changed Rust code
is recompiled on subsequent runs.

Options:
  --reconfigure  Wipe the build directory and reconfigure from scratch.
  -h|--help      Show this message.

After building, the launcher is available at:
  $BUILDDIR/src/gnome-todo
EOF
}

for arg in "$@"; do
    case "$arg" in
        --reconfigure)
            RECONFIGURE=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Error: Unknown option '$arg'." >&2
            usage >&2
            exit 1
            ;;
    esac
done

for cmd in meson ninja pkg-config; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: '$cmd' is not installed." >&2
        echo "  Debian/Ubuntu: sudo apt install meson ninja-build pkg-config" >&2
        echo "  Fedora:        sudo dnf install meson ninja-build pkgconf" >&2
        exit 1
    fi
done

MISSING_DEPS=()
for dep in gtk4 "libadwaita-1 >= 1.4"; do
    if ! pkg-config --exists $dep 2>/dev/null; then
        MISSING_DEPS+=("$dep")
    fi
done
if (( ${#MISSING_DEPS[@]} > 0 )); then
    echo "Error: missing development libraries: ${MISSING_DEPS[*]}" >&2
    echo "  Debian/Ubuntu: sudo apt install libgtk-4-dev libadwaita-1-dev" >&2
    echo "  Fedora:        sudo dnf install gtk4-devel libadwaita-devel" >&2
    exit 1
fi

if ! command -v cargo &>/dev/null; then
    echo "Warning: 'cargo' not found — the Rust core library will not be built." >&2
fi

if (( RECONFIGURE )) && [[ -d "$BUILDDIR" ]]; then
    echo "Wiping build directory..."
    rm -rf "$BUILDDIR"
fi

if [[ ! -f "$BUILDDIR/build.ninja" ]]; then
    echo "Configuring meson build..."
    meson setup "$BUILDDIR" --prefix="$INSTALLDIR"
fi

echo "Building..."
ninja -C "$BUILDDIR"

echo "Installing to $INSTALLDIR..."
ninja -C "$BUILDDIR" install

echo ""
echo "Done. Launcher: $BUILDDIR/src/gnome-todo"
