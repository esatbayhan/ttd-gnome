#!/usr/bin/env bash
# One-time development environment setup for Ubuntu/Debian.
# Safe to re-run — already-satisfied steps are skipped.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_VERSION="49"
FDO_VERSION="25.08"

section() { echo ""; echo "── $* ──"; }
ok()      { echo "  ok: $*"; }
done_()   { echo "  already done: $*"; }

# ── Distro check ──────────────────────────────────────────────────────

if ! command -v apt-get &>/dev/null; then
    echo "Warning: this script targets Ubuntu/Debian." >&2
    echo "On other distros install the equivalent packages manually." >&2
    echo "See CONTRIBUTING.md for the full list." >&2
fi

# ── System packages ───────────────────────────────────────────────────

section "System packages"
PKGS=(
    meson
    ninja-build
    pkg-config
    libgtk-4-dev
    libadwaita-1-dev
    blueprint-compiler
    flatpak
    flatpak-builder
)

MISSING=()
for pkg in "${PKGS[@]}"; do
    if ! dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -qF "install ok installed"; then
        MISSING+=("$pkg")
    fi
done

if (( ${#MISSING[@]} > 0 )); then
    echo "Installing: ${MISSING[*]}"
    sudo apt-get install -y "${MISSING[@]}"
    ok "packages installed"
else
    done_ "all system packages already installed"
fi

# ── uv ────────────────────────────────────────────────────────────────

section "uv (Python toolchain)"
if command -v uv &>/dev/null; then
    done_ "uv $(uv --version | cut -d' ' -f2) already installed"
else
    echo "Installing uv via official installer..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    ok "uv installed"
fi

# ── Python dev dependencies ───────────────────────────────────────────

section "Python dev dependencies"
cd "$SCRIPT_DIR"
uv sync
ok "venv ready (.venv/)"

# ── Git hooks ─────────────────────────────────────────────────────────

section "Git hooks"
CURRENT_HOOKS="$(git -C "$SCRIPT_DIR" config core.hooksPath 2>/dev/null || true)"
if [[ "$CURRENT_HOOKS" == ".githooks" ]]; then
    done_ "core.hooksPath already set to .githooks"
else
    git -C "$SCRIPT_DIR" config core.hooksPath .githooks
    ok "core.hooksPath → .githooks"
fi

# ── Submodules ────────────────────────────────────────────────────────

section "Git submodules"
git -C "$SCRIPT_DIR" submodule update --init --recursive
ok "submodules up to date"

# ── Flatpak remote ────────────────────────────────────────────────────

section "Flatpak remote (Flathub)"
if flatpak remote-list --user 2>/dev/null | grep -q flathub; then
    done_ "flathub remote already configured"
else
    flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
    ok "flathub remote added"
fi

# ── Flatpak runtimes ──────────────────────────────────────────────────

section "Flatpak runtimes"
for ref in org.gnome.Platform org.gnome.Sdk; do
    if flatpak info "$ref//$RUNTIME_VERSION" &>/dev/null; then
        done_ "$ref//$RUNTIME_VERSION"
    else
        echo "Installing $ref//$RUNTIME_VERSION..."
        flatpak install --user -y "$ref//$RUNTIME_VERSION"
        ok "$ref//$RUNTIME_VERSION installed"
    fi
done

EXT="org.freedesktop.Sdk.Extension.rust-stable"
if flatpak info "$EXT//$FDO_VERSION" &>/dev/null; then
    done_ "$EXT//$FDO_VERSION"
else
    echo "Installing $EXT//$FDO_VERSION..."
    flatpak install --user -y "$EXT//$FDO_VERSION"
    ok "$EXT//$FDO_VERSION installed"
fi

# ── Done ──────────────────────────────────────────────────────────────

echo ""
echo "Setup complete. Next steps:"
echo ""
echo "  Fast local build (development):"
echo "    ./dev-install.sh"
echo ""
echo "  Full Flatpak install (release testing):"
echo "    ./install.sh"
echo ""
echo "  Run tests:"
echo "    ./devtools/ci.sh"
