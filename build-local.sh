#!/usr/bin/env bash
# Build and install the app natively (without Flatpak) into ~/.local.
# Useful for development: no sandbox, hot-restartable, no flatpak-builder needed.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/builddir"
PREFIX="${PREFIX:-$HOME/.local}"

cd "$SCRIPT_DIR"

usage() {
    cat <<EOF
Usage: $0 [--clean] [--uninstall] [--prefix DIR]

Build and install $APP_ID into \$PREFIX (default: ~/.local).

Options:
  --clean      Remove the build directory before configuring.
  --uninstall  Uninstall a previously installed local build.
  --prefix DIR Set the installation prefix (default: \$HOME/.local).
  -h|--help    Show this message.

After install the app is launched with:
  gnome-todo

Ensure \$PREFIX/bin is in your PATH and that \$PREFIX/share is in
XDG_DATA_DIRS so that GNOME can find the .desktop file and icon:

  export PATH="\$HOME/.local/bin:\$PATH"
  export XDG_DATA_DIRS="\$HOME/.local/share:\${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
EOF
}

CLEAN=0
UNINSTALL=0

for arg in "$@"; do
    case "$arg" in
        --clean)
            CLEAN=1
            ;;
        --uninstall)
            UNINSTALL=1
            ;;
        --prefix)
            echo "Error: use --prefix=DIR (with =)." >&2
            exit 1
            ;;
        --prefix=*)
            PREFIX="${arg#--prefix=}"
            ;;
        -h|--help)
            APP_ID="dev.bayhan.GnomeTodo"
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

for cmd in meson ninja cargo; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: $cmd is not installed." >&2
        exit 1
    fi
done

if (( UNINSTALL )); then
    if [[ ! -f "$BUILD_DIR/install.log" ]]; then
        echo "Error: No install log found at $BUILD_DIR/install.log." >&2
        echo "       Run the build first, or remove files manually." >&2
        exit 1
    fi
    echo "Uninstalling from $PREFIX..."
    ninja -C "$BUILD_DIR" uninstall
    echo "Done."
    exit 0
fi

if (( CLEAN )) && [[ -d "$BUILD_DIR" ]]; then
    echo "Removing $BUILD_DIR..."
    rm -rf "$BUILD_DIR"
fi

if [[ ! -d "$BUILD_DIR" ]]; then
    echo "Configuring build in $BUILD_DIR (prefix: $PREFIX)..."
    meson setup "$BUILD_DIR" --prefix="$PREFIX"
fi

# Install Python dev tools (ruff, pytest) and configure git hooks.
if command -v uv &>/dev/null; then
    echo "Installing Python dev tools..."
    uv sync
fi

# Configure git to use the versioned hooks directory.
if git -C "$SCRIPT_DIR" config core.hooksPath .githooks 2>/dev/null; then
    echo "Git hooks configured (core.hooksPath = .githooks)"
fi

echo "Building..."
ninja -C "$BUILD_DIR"

echo "Installing to $PREFIX..."
ninja -C "$BUILD_DIR" install

echo ""
echo "Done. Make sure these are set in your shell profile:"
echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
echo "  export XDG_DATA_DIRS=\"\$HOME/.local/share:\${XDG_DATA_DIRS:-/usr/local/share:/usr/share}\""
echo ""
echo "Then launch with: gnome-todo"
