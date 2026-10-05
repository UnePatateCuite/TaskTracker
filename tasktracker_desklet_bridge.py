"""JSON command bridge between the Cinnamon desklet and local task database."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from typing import Any

from tasktracker import TaskNotFoundError, TaskStore, default_database_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tasktracker-desklet-bridge")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="List open tasks for the desklet")
    add_parser = commands.add_parser("add", help="Add a task from the desklet")
    add_parser.add_argument("title")
    complete_parser = commands.add_parser("complete", help="Complete a desklet task")
    complete_parser.add_argument("id", type=int)
    return parser


def run(args: argparse.Namespace, store: TaskStore) -> dict[str, Any]:
    if args.command == "list":
        tasks = store.list_tasks(status="open")
        return {"tasks": tasks, "open_count": len(tasks)}
    if args.command == "add":
        return {"task": store.add(args.title)}
    if args.command == "complete":
        return {"task": store.set_completed(args.id, True)}
    raise ValueError(f"Unsupported desklet command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run(args, TaskStore(default_database_path()))
    except (TaskNotFoundError, ValueError, OSError, sqlite3.Error) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
