"""Tests for development-only screenshot helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from devtools.screenshot import (
    ScreenshotRequest,
    build_readme_screenshot_jobs,
    parse_screenshot_options,
)


class TestScreenshotOptionParsing(unittest.TestCase):
    def test_strips_screenshot_flags_before_gapplication(self) -> None:
        argv, screenshot = parse_screenshot_options(
            [
                "gnome-todo",
                "--screenshot-output=docs/screenshots/overview-light.png",
                "--screenshot-scene=overview",
                "--screenshot-theme=light",
                "--gapplication-service",
            ]
        )

        self.assertEqual(argv, ["gnome-todo", "--gapplication-service"])
        self.assertEqual(
            screenshot,
            ScreenshotRequest(
                output_path=Path("docs/screenshots/overview-light.png"),
                scene="overview",
                theme="light",
            ),
        )

    def test_defaults_scene_and_theme_when_only_output_is_given(self) -> None:
        _argv, screenshot = parse_screenshot_options(
            [
                "gnome-todo",
                "--screenshot-output=docs/screenshots/defaults.png",
            ]
        )

        self.assertEqual(
            screenshot,
            ScreenshotRequest(
                output_path=Path("docs/screenshots/defaults.png"),
                scene="overview",
                theme="light",
            ),
        )

    def test_requires_output_for_screenshot_mode(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "--screenshot-output is required for screenshot mode"
        ):
            parse_screenshot_options(["gnome-todo", "--screenshot-scene=detail"])


class TestReadmeScreenshotJobs(unittest.TestCase):
    def test_build_jobs_is_deterministic(self) -> None:
        jobs = build_readme_screenshot_jobs(Path("docs/screenshots"))

        self.assertEqual(
            [(job.scene, job.theme, job.output_path.name) for job in jobs],
            [
                ("overview", "light", "overview-light.png"),
                ("overview", "dark", "overview-dark.png"),
                ("detail", "light", "detail-light.png"),
                ("detail", "dark", "detail-dark.png"),
                ("search", "light", "search-light.png"),
                ("search", "dark", "search-dark.png"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
