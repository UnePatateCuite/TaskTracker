"""Tkinter desktop interface for TaskTracker."""

from __future__ import annotations

import tkinter as tk
import sqlite3
from datetime import date
from tkinter import messagebox, ttk
from typing import Any

from tasktracker import PRIORITIES, TaskNotFoundError, TaskStore, validate_title


class TaskTrackerWindow:
    def __init__(self, root: tk.Tk, store: TaskStore):
        self.root = root
        self.store = store
        self.root.title("TaskTracker")
        self.root.geometry("920x620")
        self.root.minsize(700, 460)

        self.status_filter = tk.StringVar(value="all")
        self.priority_filter = tk.StringVar(value="all")
        self.search_text = tk.StringVar()
        self.count_text = tk.StringVar()

        self._configure_style()
        self._build_layout()
        self.refresh()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Treeview", rowheight=34, font=("TkDefaultFont", 10))
        style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))
        style.configure("Primary.TButton", padding=(12, 7))

    def _build_layout(self) -> None:
        outer = ttk.Frame(self.root, padding=22)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 17))
        heading = ttk.Frame(header)
        heading.pack(side="left", fill="x", expand=True)
        ttk.Label(heading, text="TaskTracker", font=("TkDefaultFont", 21, "bold")).pack(anchor="w")
        ttk.Label(heading, text="Your tasks, saved locally on this computer").pack(anchor="w", pady=(4, 0))
        ttk.Button(header, text="＋  Add task", style="Primary.TButton", command=self.add_task).pack(side="right")

        stats = ttk.Frame(outer)
        stats.pack(fill="x", pady=(0, 15))
        self.stats_labels: dict[str, ttk.Label] = {}
        for column, key, label in (
            (0, "open", "TO DO"),
            (1, "completed", "COMPLETED"),
            (2, "overdue", "OVERDUE"),
        ):
            card = ttk.LabelFrame(stats, text=label, padding=(13, 8))
            card.grid(row=0, column=column, sticky="ew", padx=(0, 9 if column < 2 else 0))
            value = ttk.Label(card, text="0", font=("TkDefaultFont", 17, "bold"))
            value.pack(anchor="w")
            self.stats_labels[key] = value
            stats.columnconfigure(column, weight=1)

        filters = ttk.Frame(outer)
        filters.pack(fill="x", pady=(0, 10))
        ttk.Label(filters, text="Show").pack(side="left", padx=(0, 7))
        status_box = ttk.Combobox(
            filters, textvariable=self.status_filter, values=("all", "open", "completed"),
            state="readonly", width=12
        )
        status_box.pack(side="left", padx=(0, 14))
        status_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh())
        ttk.Label(filters, text="Priority").pack(side="left", padx=(0, 7))
        priority_box = ttk.Combobox(
            filters, textvariable=self.priority_filter, values=("all", *PRIORITIES),
            state="readonly", width=12
        )
        priority_box.pack(side="left", padx=(0, 14))
        priority_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh())
        ttk.Label(filters, text="Search").pack(side="left", padx=(0, 7))
        search = ttk.Entry(filters, textvariable=self.search_text)
        search.pack(side="left", fill="x", expand=True)
        search.bind("<KeyRelease>", lambda _event: self.refresh())
        ttk.Button(filters, text="Clear", command=self.clear_search).pack(side="left", padx=(7, 0))

        list_frame = ttk.Frame(outer)
        list_frame.pack(fill="both", expand=True)
        columns = ("id", "title", "priority", "due", "status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        for key, title, width in (
            ("id", "ID", 55),
            ("title", "Task", 380),
            ("priority", "Priority", 100),
            ("due", "Due date", 125),
            ("status", "Status", 100),
        ):
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="w", stretch=key == "title")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.tag_configure("completed", foreground="#758078")
        self.tree.tag_configure("overdue", foreground="#a94442")
        self.tree.bind("<Double-1>", lambda _event: self.edit_task())

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(11, 0))
        self.edit_button = ttk.Button(actions, text="Edit", command=self.edit_task, state="disabled")
        self.edit_button.pack(side="left")
        self.toggle_button = ttk.Button(actions, text="Complete", command=self.toggle_completed, state="disabled")
        self.toggle_button.pack(side="left", padx=(7, 0))
        self.delete_button = ttk.Button(actions, text="Delete", command=self.delete_task, state="disabled")
        self.delete_button.pack(side="left", padx=(7, 0))
        self.tree.bind("<<TreeviewSelect>>", self._selection_changed)
        ttk.Label(actions, textvariable=self.count_text).pack(side="right")

    def _selection_changed(self, _event: Any = None) -> None:
        task = self.selected_task()
        state = "normal" if task else "disabled"
        self.edit_button.configure(state=state)
        self.delete_button.configure(state=state)
        self.toggle_button.configure(
            state=state,
            text="Reopen" if task and task["completed"] else "Complete",
        )

    def selected_task(self) -> dict[str, Any] | None:
        selection = self.tree.selection()
        if not selection:
            return None
        task_id = int(selection[0])
        try:
            return self.store.get(task_id)
        except (TaskNotFoundError, OSError, sqlite3.Error) as error:
            self._show_error(error)
            return None

    def refresh(self) -> None:
        try:
            status = self.status_filter.get()
            priority = self.priority_filter.get()
            tasks = self.store.list_tasks(
                status=status,
                priority=None if priority == "all" else priority,
                search=self.search_text.get().strip() or None,
            )
            stats = self.store.stats()
        except (OSError, sqlite3.Error) as error:
            self._show_error(error)
            return

        for item in self.tree.get_children():
            self.tree.delete(item)
        today = date.today().isoformat()
        for task in tasks:
            due = task["due_date"] or "—"
            state = "Completed" if task["completed"] else "To do"
            tags = ()
            if task["completed"]:
                tags = ("completed",)
            elif task["due_date"] and task["due_date"] < today:
                tags = ("overdue",)
            self.tree.insert(
                "", "end", iid=str(task["id"]),
                values=(task["id"], task["title"], task["priority"].title(), due, state),
                tags=tags,
            )
        for key, value in stats.items():
            if key in self.stats_labels:
                self.stats_labels[key].configure(text=str(value))
        self.count_text.set(f"{len(tasks)} task{'s' if len(tasks) != 1 else ''}")
        self._selection_changed()

    def clear_search(self) -> None:
        self.search_text.set("")
        self.refresh()

    def add_task(self) -> None:
        self._open_task_dialog()

    def edit_task(self) -> None:
        task = self.selected_task()
        if task:
            self._open_task_dialog(task)

    def _open_task_dialog(self, task: dict[str, Any] | None = None) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit task" if task else "Add task")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Task name").grid(row=0, column=0, sticky="w", pady=(0, 5))
        title_var = tk.StringVar(value=task["title"] if task else "")
        title_entry = ttk.Entry(frame, textvariable=title_var, width=48)
        title_entry.grid(row=1, column=0, sticky="ew")

        ttk.Label(frame, text="Description (optional)").grid(row=2, column=0, sticky="w", pady=(12, 5))
        description = tk.Text(frame, width=48, height=4, wrap="word")
        description.grid(row=3, column=0, sticky="ew")
        if task:
            description.insert("1.0", task["description"])

        options = ttk.Frame(frame)
        options.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(options, text="Priority").grid(row=0, column=0, sticky="w", padx=(0, 7))
        priority_var = tk.StringVar(value=task["priority"] if task else "medium")
        ttk.Combobox(
            options, textvariable=priority_var, values=PRIORITIES, state="readonly", width=12
        ).grid(row=0, column=1, sticky="w")
        ttk.Label(options, text="Due date (YYYY-MM-DD)").grid(row=0, column=2, sticky="w", padx=(18, 7))
        due_var = tk.StringVar(value=task["due_date"] or "" if task else "")
        ttk.Entry(options, textvariable=due_var, width=15).grid(row=0, column=3, sticky="w")

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, sticky="e", pady=(16, 0))
        ttk.Button(buttons, text="Cancel", command=dialog.destroy).pack(side="right")

        def save() -> None:
            try:
                title = validate_title(title_var.get())
                values = {
                    "title": title,
                    "description": description.get("1.0", "end-1c").strip(),
                    "priority": priority_var.get(),
                    "due_date": due_var.get().strip() or None,
                }
                if task:
                    self.store.update(task["id"], values)
                else:
                    self.store.add(
                        values["title"], values["description"], values["priority"], values["due_date"]
                    )
            except (ValueError, TaskNotFoundError, OSError, sqlite3.Error) as error:
                self._show_error(error, parent=dialog)
                return
            dialog.destroy()
            self.refresh()

        ttk.Button(buttons, text="Save task", command=save).pack(side="right", padx=(0, 7))
        title_entry.focus_set()
        dialog.bind("<Return>", lambda _event: save())
        self.root.wait_window(dialog)

    def toggle_completed(self) -> None:
        task = self.selected_task()
        if not task:
            return
        try:
            self.store.set_completed(task["id"], not bool(task["completed"]))
        except (TaskNotFoundError, OSError, sqlite3.Error) as error:
            self._show_error(error)
            return
        self.refresh()

    def delete_task(self) -> None:
        task = self.selected_task()
        if not task:
            return
        if not messagebox.askyesno("Delete task", f'Delete "{task["title"]}"?', parent=self.root):
            return
        try:
            self.store.delete(task["id"])
        except (TaskNotFoundError, OSError, sqlite3.Error) as error:
            self._show_error(error)
            return
        self.refresh()

    def _show_error(self, error: Exception, parent: tk.Misc | None = None) -> None:
        messagebox.showerror("TaskTracker error", str(error), parent=parent or self.root)


def launch(store: TaskStore) -> None:
    root = tk.Tk()
    TaskTrackerWindow(root, store)
    root.mainloop()
