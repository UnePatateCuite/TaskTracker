import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from tasktracker import TaskNotFoundError, TaskStore, build_parser
from tasktracker_desklet_bridge import build_parser as build_bridge_parser
from tasktracker_desklet_bridge import run as run_bridge


class TaskStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = TaskStore(Path(self.temp_dir.name) / "tasks.sqlite3")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_get_task(self):
        task = self.store.add("  Plan release  ", "Write release notes", "high")
        self.assertEqual(task["title"], "Plan release")
        self.assertEqual(task["description"], "Write release notes")
        self.assertEqual(self.store.get(task["id"])["priority"], "high")

    def test_list_filters_by_status_priority_and_search(self):
        urgent = self.store.add("Prepare proposal", "For next week", priority="high")
        self.store.add("Buy groceries", priority="low")
        self.store.set_completed(urgent["id"], True)

        self.assertEqual(len(self.store.list_tasks(status="completed")), 1)
        self.assertEqual(len(self.store.list_tasks(status="open", priority="low")), 1)
        self.assertEqual(len(self.store.list_tasks(search="NEXT WEEK")), 1)

    def test_update_and_delete(self):
        task = self.store.add("Draft")
        updated = self.store.update(task["id"], {"title": "Final draft", "due_date": "2026-12-31"})
        self.assertEqual(updated["title"], "Final draft")
        self.assertEqual(updated["due_date"], "2026-12-31")
        self.store.delete(task["id"])
        with self.assertRaises(TaskNotFoundError):
            self.store.get(task["id"])

    def test_stats_include_overdue_tasks(self):
        overdue = (date.today() - timedelta(days=1)).isoformat()
        self.store.add("Late task", due_date=overdue)
        self.store.add("Finished task")
        self.store.set_completed(2, True)
        self.assertEqual(self.store.stats(), {"total": 2, "open": 1, "completed": 1, "overdue": 1})

    def test_validation_rejects_bad_title_and_date(self):
        with self.assertRaises(ValueError):
            self.store.add("  ")
        with self.assertRaises(ValueError):
            self.store.add("Bad date", due_date="2026-02-30")
        with self.assertRaises(ValueError):
            self.store.add("Noncanonical date", due_date="20261005")

    def test_no_command_selects_desktop_app(self):
        self.assertIsNone(build_parser().parse_args([]).command)

    def test_desklet_bridge_lists_adds_and_completes_tasks(self):
        args = build_bridge_parser().parse_args(["add", "Panel task"])
        added = run_bridge(args, self.store)
        task_id = added["task"]["id"]

        listed = run_bridge(build_bridge_parser().parse_args(["list"]), self.store)
        self.assertEqual(listed["open_count"], 1)
        self.assertEqual(listed["tasks"][0]["title"], "Panel task")

        completed = run_bridge(
            build_bridge_parser().parse_args(["complete", str(task_id)]), self.store
        )
        self.assertEqual(completed["task"]["completed"], 1)
        self.assertEqual(run_bridge(build_bridge_parser().parse_args(["list"]), self.store)["open_count"], 0)


if __name__ == "__main__":
    unittest.main()
