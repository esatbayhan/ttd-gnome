"""Development-only screenshot helpers for README automation."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

try:
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gdk, GLib, Graphene, Gtk
except ImportError:
    Adw = Gdk = GLib = Graphene = Gtk = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from gnome_todo._window import TodoWindow

SCREENSHOT_SCENES = ("overview", "detail", "search")
SCREENSHOT_THEMES = ("light", "dark")
_DETAIL_TASK_TEXT = "Polish release checklist"
_SEARCH_QUERY = "release"


@dataclass(frozen=True)
class ScreenshotRequest:
    """Information needed to capture a single screenshot."""

    output_path: Path
    scene: str
    theme: str


@dataclass(frozen=True)
class ReadmeScreenshotJob:
    """One README screenshot variant."""

    scene: str
    theme: str
    output_path: Path


def parse_screenshot_options(
    argv: Sequence[str],
) -> tuple[list[str], ScreenshotRequest | None]:
    """Parse development-only screenshot flags."""
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--screenshot-output")
    parser.add_argument("--screenshot-scene")
    parser.add_argument("--screenshot-theme")

    namespace, remaining = parser.parse_known_args(argv[1:])
    screenshot_requested = any(
        value is not None
        for value in (
            namespace.screenshot_output,
            namespace.screenshot_scene,
            namespace.screenshot_theme,
        )
    )

    screenshot: ScreenshotRequest | None = None
    if screenshot_requested:
        if namespace.screenshot_output is None:
            raise ValueError("--screenshot-output is required for screenshot mode")

        scene = namespace.screenshot_scene or "overview"
        theme = namespace.screenshot_theme or "light"

        if scene not in SCREENSHOT_SCENES:
            raise ValueError(f"--screenshot-scene must be one of: {', '.join(SCREENSHOT_SCENES)}")
        if theme not in SCREENSHOT_THEMES:
            raise ValueError(f"--screenshot-theme must be one of: {', '.join(SCREENSHOT_THEMES)}")

        screenshot = ScreenshotRequest(
            output_path=Path(namespace.screenshot_output),
            scene=scene,
            theme=theme,
        )

    return [argv[0], *remaining], screenshot


def prepare_window_for_screenshot(
    window: TodoWindow,
    screenshot: ScreenshotRequest,
) -> None:
    """Apply deterministic scene and theme state before capture."""
    _apply_theme(screenshot.theme)
    _reset_window_state(window)

    if screenshot.scene == "overview":
        return
    if screenshot.scene == "detail":
        task = _find_task(window, _DETAIL_TASK_TEXT)
        if task is None:
            raise ValueError(f"Could not find screenshot detail task: {_DETAIL_TASK_TEXT}")
        window._on_task_selected(task)
        return
    if screenshot.scene == "search":
        window.search_btn.set_active(True)
        window.search_entry.set_text(_SEARCH_QUERY)
        return
    raise ValueError(f"Unsupported screenshot scene: {screenshot.scene}")


def schedule_screenshot_capture(
    app: Adw.Application,
    window: TodoWindow,
    screenshot: ScreenshotRequest,
    set_exit_code: Callable[[int], None],
) -> None:
    """Capture the window after it has rendered a couple of frames."""
    state = {"ready_ticks": 0}

    def on_tick(widget: Gtk.Widget, _clock: Gdk.FrameClock) -> bool:
        if not widget.get_mapped():
            return GLib.SOURCE_CONTINUE
        if widget.get_width() <= 0 or widget.get_height() <= 0:
            return GLib.SOURCE_CONTINUE

        state["ready_ticks"] += 1
        if state["ready_ticks"] < 2:
            return GLib.SOURCE_CONTINUE

        try:
            take_window_screenshot(window, screenshot.output_path)
            print(f"[screenshot] saved {screenshot.output_path}")
        except Exception as exc:
            print(f"[screenshot] {exc}", file=sys.stderr)
            set_exit_code(1)
        app.quit()
        return GLib.SOURCE_REMOVE

    window.add_tick_callback(on_tick)


def build_readme_screenshot_jobs(output_dir: Path) -> list[ReadmeScreenshotJob]:
    """Return the deterministic README screenshot matrix."""
    return [
        ReadmeScreenshotJob(
            scene=scene,
            theme=theme,
            output_path=output_dir / f"{scene}-{theme}.png",
        )
        for scene in SCREENSHOT_SCENES
        for theme in SCREENSHOT_THEMES
    ]


def take_window_screenshot(window: Gtk.Window, output_path: Path) -> None:
    """Render *window* to *output_path* using GTK's own renderer."""
    width = window.get_width()
    height = window.get_height()
    if width <= 0 or height <= 0:
        raise RuntimeError("Window size is not ready yet")

    snapshot = Gtk.Snapshot.new()
    Gtk.Widget.do_snapshot(window, snapshot)
    node = snapshot.to_node()
    if node is None:
        raise RuntimeError("GTK snapshot produced no render node")

    native = window.get_native()
    if native is None:
        raise RuntimeError("Window has no native surface yet")

    renderer = native.get_renderer()
    if renderer is None:
        raise RuntimeError("Window renderer is unavailable")

    bounds = Graphene.Rect().init(0, 0, float(width), float(height))
    texture = renderer.render_texture(node, bounds)
    if texture is None:
        raise RuntimeError("Renderer did not return a texture")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not texture.save_to_png(str(output_path)):
        raise RuntimeError(f"Failed to save PNG to {output_path}")


def _apply_theme(theme: str) -> None:
    style_manager = Adw.StyleManager.get_default()
    if theme == "light":
        style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        return
    if theme == "dark":
        style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        return
    raise ValueError(f"Unsupported screenshot theme: {theme}")


def _reset_window_state(window: TodoWindow) -> None:
    window._selection_kind = "smart"
    window._selection_value = "All"
    window._show_completed_in_list = False
    window._set_filter_active("All")
    window.project_list.unselect_all()
    window.context_list.unselect_all()
    window._close_detail_panel()
    window.search_btn.set_active(False)
    window.search_entry.set_text("")
    window._refresh_content()


def _find_task(window: TodoWindow, text: str) -> object | None:
    needle = text.lower()
    return next(
        (task for task in window._all_tasks() if needle in task.text.lower()),
        None,
    )
