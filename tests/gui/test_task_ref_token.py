"""Tests for drag-and-drop TaskRef serialization in gnome_todo._core."""

from __future__ import annotations

import unittest

from ttd_core.task import TaskRef

from gnome_todo._core import task_ref_from_token, task_ref_to_token


class TestTaskRefToken(unittest.TestCase):
    def test_round_trips_valid_token(self) -> None:
        ref = TaskRef("done.txt.d/task.txt", 3)

        parsed = task_ref_from_token(task_ref_to_token(ref))

        self.assertEqual(parsed, ref)

    def test_rejects_non_json_tokens(self) -> None:
        with self.assertRaises(ValueError):
            task_ref_from_token("not json")

    def test_rejects_non_object_payloads(self) -> None:
        with self.assertRaises(ValueError):
            task_ref_from_token("[]")

    def test_rejects_missing_line_index(self) -> None:
        with self.assertRaises(ValueError):
            task_ref_from_token('{"relative_path":"task.txt"}')

    def test_rejects_negative_line_index(self) -> None:
        with self.assertRaises(ValueError):
            task_ref_from_token('{"relative_path":"task.txt","line_index":-1}')

    def test_rejects_path_traversal(self) -> None:
        with self.assertRaises(ValueError):
            task_ref_from_token('{"relative_path":"../outside.txt","line_index":0}')


if __name__ == "__main__":
    unittest.main()
