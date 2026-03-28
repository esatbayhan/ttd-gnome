#!/usr/bin/env bash
# Build and install the Flatpak app and GNOME Shell extension.
set -euo pipefail

APP_ID="dev.bayhan.GnomeTodo"
MANIFEST="$APP_ID.json"
BUILD_DIR="build-dir"
STATE_DIR=".flatpak-builder"
RUNTIME_VERSION="49"
# FDO SDK version that hosts the Rust extension (GNOME 49 → FDO 25.08).
# Update this alongside runtime-version when bumping the GNOME SDK.
FDO_VERSION="25.08"
REFRESH_SOURCES=0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

usage() {
    cat <<EOF
Usage: $0 [--refresh-sources]

Builds and installs the Flatpak app ($APP_ID) and the GNOME Shell extension.

Options:
  --refresh-sources  Update cached VCS sources such as blueprint-compiler.
  -h|--help          Show this message.

After install:
  flatpak run $APP_ID
EOF
}

for arg in "$@"; do
    case "$arg" in
        --refresh-sources)
            REFRESH_SOURCES=1
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

for cmd in flatpak flatpak-builder; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: $cmd is not installed." >&2
        exit 1
    fi
done

# Ensure user-level Flathub remote is configured.
if ! flatpak remote-list --user | grep -q flathub; then
    echo "Adding Flathub user remote..."
    flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
fi

# Ensure runtime, SDK, and required SDK extensions are installed.
for ref in org.gnome.Platform org.gnome.Sdk; do
    if ! flatpak info "$ref//$RUNTIME_VERSION" &>/dev/null; then
        echo "Installing $ref $RUNTIME_VERSION..."
        flatpak install --user -y "$ref//$RUNTIME_VERSION"
    fi
done

EXT="org.freedesktop.Sdk.Extension.rust-stable"
if ! flatpak info "$EXT//$FDO_VERSION" &>/dev/null; then
    echo "Installing $EXT $FDO_VERSION..."
    flatpak install --user -y "$EXT//$FDO_VERSION"
fi

download_args=(
    --download-only
    --force-clean
    --state-dir="$STATE_DIR"
)

if (( REFRESH_SOURCES )); then
    echo "Refreshing cached dependency sources..."
else
    echo "Reusing cached dependency sources..."
    download_args+=(--disable-updates)
fi

flatpak-builder "${download_args[@]}" "$BUILD_DIR" "$MANIFEST"

echo "Building $APP_ID..."
flatpak-builder \
    --user \
    --install \
    --state-dir="$STATE_DIR" \
    --force-clean \
    --disable-download \
    "$BUILD_DIR" "$MANIFEST"

"$SCRIPT_DIR/install-extension.sh"

echo ""
echo "Done. Launch with: flatpak run $APP_ID"
