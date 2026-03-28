#!/usr/bin/env python3
"""Generate the README screenshot gallery from committed demo data."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
APP_ID = "dev.bayhan.GnomeTodo"
sys.path.insert(0, str(ROOT / "src"))

from devtools.screenshot import build_readme_screenshot_jobs  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate README screenshots from the demo todo.txt.d fixture."
    )
    parser.add_argument(
        "--launcher",
        help=(
            "Command used to launch the app. Defaults to builddir/src/gnome-todo, "
            "then a gnome-todo executable in PATH."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "docs" / "screenshots"),
        help="Directory where PNG files are written.",
    )
    parser.add_argument(
        "--fixtures-dir",
        default=str(ROOT / "devtools" / "fixtures" / "screenshots"),
        help="Directory pointing at the demo todo.txt.d root.",
    )
    return parser.parse_args()


def _resolve_launcher(explicit: str | None) -> list[str]:
    if explicit:
        return shlex.split(explicit)

    local_launcher = ROOT / "builddir" / "src" / "gnome-todo"
    if local_launcher.exists():
        return [str(local_launcher)]

    installed_launcher = shutil.which("gnome-todo")
    if installed_launcher is not None:
        return [installed_launcher]

    flatpak = shutil.which("flatpak")
    if flatpak is not None:
        result = subprocess.run(
            [flatpak, "info", APP_ID],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0:
            return [flatpak, "run", APP_ID]

    raise SystemExit(
        "No launcher found. Build the project first with "
        "`meson setup build-dir && meson compile -C build-dir`, "
        "install/run the Flatpak locally, or pass --launcher."
    )


def _kill_existing_instance(launcher: list[str]) -> None:
    if launcher[:2] != ["flatpak", "run"]:
        return
    subprocess.run(
        ["flatpak", "kill", APP_ID],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def _flatten_backgrounds(output_dir: Path) -> None:
    backgrounds = {
        "light": (255, 255, 255, 255),
        "dark": (48, 48, 52, 255),
    }
    for path in output_dir.glob("*.png"):
        theme = "dark" if path.stem.endswith("-dark") else "light"
        image = Image.open(path).convert("RGBA")
        background = Image.new("RGBA", image.size, backgrounds[theme])
        flattened = Image.alpha_composite(background, image).convert("RGB")
        flattened.save(path)


def main() -> int:
    args = _parse_args()
    launcher = _resolve_launcher(args.launcher)
    output_dir = Path(args.output_dir).resolve()
    fixtures_dir = Path(args.fixtures_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    jobs = build_readme_screenshot_jobs(output_dir)
    _kill_existing_instance(launcher)
    with tempfile.TemporaryDirectory(prefix="gnome-todo-screenshot-config-") as config_dir:
        env = os.environ.copy()
        env["TODO_DIR"] = str(fixtures_dir)
        env["XDG_CONFIG_HOME"] = config_dir

        for job in jobs:
            cmd = [
                *launcher,
                f"--screenshot-output={job.output_path}",
                f"--screenshot-scene={job.scene}",
                f"--screenshot-theme={job.theme}",
            ]
            print(f"[screenshots] {job.scene}/{job.theme} -> {job.output_path}")
            subprocess.run(cmd, cwd=ROOT, env=env, check=True)

    _flatten_backgrounds(output_dir)
    print(f"[screenshots] wrote {len(jobs)} files to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
