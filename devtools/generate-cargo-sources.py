#!/usr/bin/env python3
"""Generate cargo-sources.json from vendor/ttd-core/Cargo.lock.

flatpak-builder uses this file to pre-fetch all Rust crate archives during
its download phase so the build can proceed completely offline inside the
Flatpak sandbox.

Run this script whenever Cargo.lock changes:

    python3 devtools/generate-cargo-sources.py

The generated cargo-sources.json is committed to the repository.

No network access or third-party packages are required — checksums are read
directly from Cargo.lock (which records the sha256 of every .crate archive).
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARGO_LOCK = ROOT / "vendor" / "ttd-core" / "Cargo.lock"
OUTPUT = ROOT / "cargo-sources.json"
CRATES_IO = "https://static.crates.io/crates"


def main() -> None:
    if not CARGO_LOCK.exists():
        print(f"Error: {CARGO_LOCK} not found.", file=sys.stderr)
        sys.exit(1)

    lock = tomllib.loads(CARGO_LOCK.read_text(encoding="utf-8"))
    sources: list[dict] = []

    for pkg in lock.get("package", []):
        if not pkg.get("source", "").startswith("registry+"):
            continue
        checksum = pkg.get("checksum")
        if not checksum:
            continue
        name = pkg["name"]
        version = pkg["version"]
        sources.append(
            {
                "type": "archive",
                "archive-type": "tar-gzip",
                "url": f"{CRATES_IO}/{name}/{name}-{version}.crate",
                "sha256": checksum,
                "dest": f"cargo-vendor/{name}-{version}",
            }
        )

    # Cargo config that redirects crates-io to the vendored directory.
    # flatpak-builder places this at .cargo/config inside the build environment.
    sources.append(
        {
            "type": "inline",
            "contents": (
                "[source.crates-io]\n"
                'replace-with = "vendored-sources"\n\n'
                "[source.vendored-sources]\n"
                'directory = "cargo-vendor"\n'
            ),
            "dest": ".cargo",
            "dest-filename": "config",
        }
    )

    OUTPUT.write_text(json.dumps(sources, indent=2) + "\n", encoding="utf-8")
    crate_count = len(sources) - 1  # exclude the inline config entry
    print(f"Wrote {crate_count} crate sources → {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
