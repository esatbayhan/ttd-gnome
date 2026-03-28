#!/usr/bin/env bash
# Local CI: lint, format check, and tests.
# Exits 0 only if all checks pass.
#
# Requires: uv — https://docs.astral.sh/uv/
# Run manually at any time, or automatically via the pre-commit hook.
#
# First-time setup: uv sync

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# ── Tool selection ────────────────────────────────────────────────────

if command -v uv &>/dev/null; then
    RUFF=(uv run ruff)
    PYTEST=(uv run pytest)
elif command -v ruff &>/dev/null && command -v pytest &>/dev/null; then
    RUFF=(ruff)
    PYTEST=(pytest)
else
    echo "ci: 'uv' is required to run checks." >&2
    echo "  Install: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

# ── Checks ────────────────────────────────────────────────────────────

ERRORS=0

run_check() {
    local label="$1"; shift
    printf "  %-26s" "$label"
    local out rc=0
    out=$("$@" 2>&1) || rc=$?
    if (( rc == 0 )); then
        echo "pass"
    else
        echo "FAIL"
        printf "%s\n" "$out" | sed 's/^/    /'
        ERRORS=$(( ERRORS + 1 ))
    fi
}

echo "Running CI checks..."
run_check "ruff check"   "${RUFF[@]}"   check .
run_check "ruff format"  "${RUFF[@]}"   format --check .
run_check "pytest"       "${PYTEST[@]}"

# ── Result ────────────────────────────────────────────────────────────

echo ""
if (( ERRORS > 0 )); then
    echo "CI failed ($ERRORS check(s) did not pass)."
    exit 1
fi

echo "All checks passed."
