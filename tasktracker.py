#!/usr/bin/env python3
"""A local desktop and command-line task tracker backed by SQLite."""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any, Iterator


PRIORITIES = ("low", "medium", "high")
DB_ENVIRONMENT_VARIABLE = "TASKTRACKER_DB"


class TaskNotFoundError(Exception):
    """Raised when a task ID does not exist."""


class TaskStore:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 120),
                    description TEXT NOT NULL DEFAULT '',
                    priority TEXT NOT NULL CHECK(priority IN ('low', 'medium', 'high')),
                    due_date TEXT,
                    completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0, 1)),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def add(
        self, title: str, description: str = "", priority: str = "medium", due_date: str | None = None
    ) -> dict[str, Any]:
        title = validate_title(title)
        validate_priority(priority)
        validate_due_date(due_date)
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO tasks (title, description, priority, due_date) VALUES (?, ?, ?, ?)",
                (title, description.strip(), priority, due_date),
            )
            task_id = cursor.lastrowid
        return self.get(task_id)

    def get(self, task_id: int) -> dict[str, Any]:
        with self.connect() as connection:
            task = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if task is None:
            raise TaskNotFoundError(f"No task found with ID {task_id}.")
        return dict(task)

    def list_tasks(
        self,
        status: str = "all",
        priority: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        parameters: list[Any] = []
        if status == "open":
            conditions.append("completed = 0")
        elif status == "completed":
            conditions.append("completed = 1")
        if priority:
            validate_priority(priority)
            conditions.append("priority = ?")
            parameters.append(priority)
        if search:
            conditions.append("(instr(lower(title), lower(?)) > 0 OR instr(lower(description), lower(?)) > 0)")
            parameters.extend((search, search))
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM tasks
                {where}
                ORDER BY completed ASC, due_date IS NULL ASC, due_date ASC, id ASC
                """,
                parameters,
            ).fetchall()
        return [dict(row) for row in rows]

    def update(self, task_id: int, changes: dict[str, Any]) -> dict[str, Any]:
        if not changes:
            raise ValueError("Provide at least one field to update.")
        if "title" in changes:
            changes["title"] = validate_title(changes["title"])
        if "priority" in changes:
            validate_priority(changes["priority"])
        if "due_date" in changes:
            validate_due_date(changes["due_date"])
        allowed_columns = {"title", "description", "priority", "due_date"}
        if not changes.keys() <= allowed_columns:
            raise ValueError("Invalid task field.")
        assignments = ", ".join(f"{column} = ?" for column in changes)
        values = list(changes.values())
        values.append(task_id)
        with self.connect() as connection:
            cursor = connection.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", values)
        if cursor.rowcount == 0:
            raise TaskNotFoundError(f"No task found with ID {task_id}.")
        return self.get(task_id)

    def set_completed(self, task_id: int, completed: bool) -> dict[str, Any]:
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE tasks SET completed = ? WHERE id = ?", (int(completed), task_id)
            )
        if cursor.rowcount == 0:
            raise TaskNotFoundError(f"No task found with ID {task_id}.")
        return self.get(task_id)

    def delete(self, task_id: int) -> None:
        with self.connect() as connection:
            cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            raise TaskNotFoundError(f"No task found with ID {task_id}.")

    def stats(self) -> dict[str, int]:
        today = date.today().isoformat()
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(completed = 0), 0) AS open,
                    COALESCE(SUM(completed = 1), 0) AS completed,
                    COALESCE(SUM(completed = 0 AND due_date IS NOT NULL AND due_date < ?), 0) AS overdue
                FROM tasks
                """,
                (today,),
            ).fetchone()
        return {key: int(row[key]) for key in ("total", "open", "completed", "overdue")}


def validate_title(title: str) -> str:
    title = title.strip()
    if not title:
        raise ValueError("Task title cannot be empty.")
    if len(title) > 120:
        raise ValueError("Task title cannot exceed 120 characters.")
    return title


def validate_priority(priority: str) -> None:
    if priority not in PRIORITIES:
        raise ValueError(f"Priority must be one of: {', '.join(PRIORITIES)}.")


def validate_due_date(value: str | None) -> None:
    if value is None:
        return
    try:
        parsed_date = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("Due date must be a real date in YYYY-MM-DD format.") from error
    if parsed_date.isoformat() != value:
        raise ValueError("Due date must be a real date in YYYY-MM-DD format.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tasktracker",
        description="Manage your tasks locally. Tasks are saved in an SQLite database on this computer.",
    )
    commands = parser.add_subparsers(dest="command")

    add_parser = commands.add_parser("add", help="Create a task")
    add_parser.add_argument("title", help="Task title (up to 120 characters)")
    add_parser.add_argument("-d", "--description", default="", help="Optional task description")
    add_parser.add_argument("-p", "--priority", choices=PRIORITIES, default="medium")
    add_parser.add_argument("--due", help="Due date in YYYY-MM-DD format")

    list_parser = commands.add_parser("list", help="List and filter tasks")
    list_parser.add_argument("--status", choices=("all", "open", "completed"), default="all")
    list_parser.add_argument("--priority", choices=PRIORITIES)
    list_parser.add_argument("--search", help="Search task titles and descriptions")

    show_parser = commands.add_parser("show", help="Show a task's details")
    show_parser.add_argument("id", type=int, help="Task ID")

    edit_parser = commands.add_parser("edit", help="Edit a task")
    edit_parser.add_argument("id", type=int, help="Task ID")
    edit_parser.add_argument("--title", help="New task title")
    description_group = edit_parser.add_mutually_exclusive_group()
    description_group.add_argument("--description", help="Replace the task description")
    description_group.add_argument("--clear-description", action="store_true", help="Remove the description")
    edit_parser.add_argument("--priority", choices=PRIORITIES)
    due_group = edit_parser.add_mutually_exclusive_group()
    due_group.add_argument("--due", help="Set due date in YYYY-MM-DD format")
    due_group.add_argument("--clear-due", action="store_true", help="Remove the due date")

    complete_parser = commands.add_parser("complete", help="Mark a task completed")
    complete_parser.add_argument("id", type=int, help="Task ID")

    reopen_parser = commands.add_parser("reopen", help="Reopen a completed task")
    reopen_parser.add_argument("id", type=int, help="Task ID")

    delete_parser = commands.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("id", type=int, help="Task ID")
    delete_parser.add_argument("--yes", action="store_true", help="Delete without asking for confirmation")

    commands.add_parser("stats", help="Show task counts")
    return parser


def format_task(task: dict[str, Any], detailed: bool = False) -> str:
    status = "x" if task["completed"] else " "
    due = task["due_date"] or "no due date"
    output = f"[{status}] #{task['id']} [{task['priority']}] {due}  {task['title']}"
    if detailed:
        if task["description"]:
            output += f"\n    {task['description']}"
        output += f"\n    Status: {'completed' if task['completed'] else 'open'}"
    return output


def run(args: argparse.Namespace, store: TaskStore) -> int:
    if args.command == "add":
        task = store.add(args.title, args.description, args.priority, args.due)
        print(f"Added task:\n{format_task(task, detailed=True)}")
    elif args.command == "list":
        tasks = store.list_tasks(args.status, args.priority, args.search)
        if not tasks:
            print("No tasks found.")
        else:
            for task in tasks:
                print(format_task(task))
        print(f"\n{len(tasks)} task{'s' if len(tasks) != 1 else ''}")
    elif args.command == "show":
        print(format_task(store.get(args.id), detailed=True))
    elif args.command == "edit":
        changes: dict[str, Any] = {}
        if args.title is not None:
            changes["title"] = args.title
        if args.description is not None:
            changes["description"] = args.description.strip()
        elif args.clear_description:
            changes["description"] = ""
        if args.priority is not None:
            changes["priority"] = args.priority
        if args.due is not None:
            changes["due_date"] = args.due
        elif args.clear_due:
            changes["due_date"] = None
        task = store.update(args.id, changes)
        print(f"Updated task:\n{format_task(task, detailed=True)}")
    elif args.command == "complete":
        task = store.set_completed(args.id, True)
        print(f"Completed: {task['title']}")
    elif args.command == "reopen":
        task = store.set_completed(args.id, False)
        print(f"Reopened: {task['title']}")
    elif args.command == "delete":
        task = store.get(args.id)
        if not args.yes:
            answer = input(f'Delete "{task["title"]}"? [y/N] ').strip().lower()
            if answer not in ("y", "yes"):
                print("Deletion cancelled.")
                return 0
        store.delete(args.id)
        print(f"Deleted task #{args.id}.")
    elif args.command == "stats":
        summary = store.stats()
        print(
            f"Total: {summary['total']}  |  To do: {summary['open']}  |  "
            f"Completed: {summary['completed']}  |  Overdue: {summary['overdue']}"
        )
    return 0


def default_database_path() -> Path:
    configured_path = os.environ.get(DB_ENVIRONMENT_VARIABLE)
    if configured_path:
        return Path(configured_path).expanduser()
    return Path.home() / ".tasktracker" / "tasks.sqlite3"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        store = TaskStore(default_database_path())
        if args.command is None:
            from tasktracker_ui import launch

            launch(store)
            return 0
        return run(args, store)
    except ModuleNotFoundError as error:
        if error.name == "tkinter":
            print(
                "Error: Tkinter is needed for the desktop window. On Ubuntu or Debian, install it with:\n"
                "  sudo apt install python3-tk",
                file=sys.stderr,
            )
            return 1
        raise
    except (TaskNotFoundError, ValueError, OSError, sqlite3.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
