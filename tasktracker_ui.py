"""Tkinter desktop interface for TaskTracker."""

from __future__ import annotations

import sqlite3
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk
from typing import Any

from tasktracker import PRIORITIES, TaskNotFoundError, TaskStore, validate_title


COLORS = {
    "background": "#f4f6f5",
    "surface": "#ffffff",
    "ink": "#202b27",
    "muted": "#818d87",
    "line": "#e8edea",
    "green": "#28785d",
    "green_hover": "#21644d",
    "green_soft": "#eaf3ee",
    "red": "#b9554d",
    "red_soft": "#fbefed",
    "amber": "#a57431",
    "amber_soft": "#f8f2e7",
    "blue": "#5479a8",
    "blue_soft": "#edf2f8",
}

PRIORITY_COLORS = {
    "high": ("#a94f48", "#faeeec"),
    "medium": ("#98702f", "#f8f2e7"),
    "low": ("#47745d", "#eaf3ee"),
}


class TaskTrackerWindow:
    def __init__(self, root: tk.Tk, store: TaskStore):
        self.root = root
        self.store = store
        self.root.title("TaskTracker")
        self.root.geometry("1000x740")
        self.root.minsize(760, 560)
        self.root.configure(background=COLORS["background"])

        self.status_filter = tk.StringVar(value="all")
        self.priority_filter = tk.StringVar(value="all")
        self.search_text = tk.StringVar()
        self.count_text = tk.StringVar()
        self.tab_buttons: dict[str, tk.Button] = {}
        self.stat_values: dict[str, tk.Label] = {}

        self._configure_style()
        self._build_layout()
        self.refresh()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(
            "Task.TCombobox",
            fieldbackground=COLORS["surface"],
            background=COLORS["surface"],
            foreground=COLORS["ink"],
            arrowcolor=COLORS["muted"],
            bordercolor=COLORS["line"],
            lightcolor=COLORS["line"],
            darkcolor=COLORS["line"],
            padding=(8, 7),
            font=("TkDefaultFont", 10),
        )

    def _build_layout(self) -> None:
        outer = tk.Frame(self.root, background=COLORS["background"])
        outer.pack(fill="both", expand=True, padx=42, pady=(29, 22))

        header = tk.Frame(outer, background=COLORS["background"])
        header.pack(fill="x", pady=(0, 23))
        brand = tk.Frame(header, background=COLORS["background"])
        brand.pack(side="left", fill="x", expand=True)
        tk.Label(
            brand, text="✓", background=COLORS["green"], foreground="white",
            font=("TkDefaultFont", 13, "bold"), width=2, height=1,
        ).pack(side="left", padx=(0, 10), ipady=3)
        brand_text = tk.Frame(brand, background=COLORS["background"])
        brand_text.pack(side="left")
        tk.Label(
            brand_text, text="TaskTracker", background=COLORS["background"],
            foreground=COLORS["ink"], font=("TkDefaultFont", 14, "bold"),
        ).pack(anchor="w")
        tk.Label(
            brand_text, text="YOUR PERSONAL WORKSPACE", background=COLORS["background"],
            foreground=COLORS["muted"], font=("TkDefaultFont", 8, "bold"),
        ).pack(anchor="w", pady=(2, 0))
        self._button(header, "＋  Add task", self.add_task, primary=True).pack(side="right", ipady=3)

        title_row = tk.Frame(outer, background=COLORS["background"])
        title_row.pack(fill="x", pady=(0, 19))
        title_block = tk.Frame(title_row, background=COLORS["background"])
        title_block.pack(side="left")
        tk.Label(
            title_block, text="Make room for what matters.", background=COLORS["background"],
            foreground=COLORS["ink"], font=("TkDefaultFont", 23, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_block, text="A little progress each day adds up to big results.",
            background=COLORS["background"], foreground=COLORS["muted"],
            font=("TkDefaultFont", 10),
        ).pack(anchor="w", pady=(5, 0))
        today_text = date.today().strftime("%A, %B %d").replace(" 0", " ")
        tk.Label(
            title_row, text=today_text, background=COLORS["background"],
            foreground=COLORS["muted"], font=("TkDefaultFont", 9, "bold"),
        ).pack(side="right", anchor="s", pady=(0, 4))

        self._build_stats(outer)
        self._build_task_panel(outer)

    def _build_stats(self, parent: tk.Widget) -> None:
        stats = tk.Frame(parent, background=COLORS["background"])
        stats.pack(fill="x", pady=(0, 19))
        definitions = (
            ("open", "TO DO", COLORS["green"], COLORS["green_soft"]),
            ("completed", "COMPLETED", COLORS["blue"], COLORS["blue_soft"]),
            ("overdue", "OVERDUE", COLORS["red"], COLORS["red_soft"]),
        )
        for index, (key, label, accent, tint) in enumerate(definitions):
            card = tk.Frame(stats, background=COLORS["surface"], highlightthickness=1,
                            highlightbackground=COLORS["line"], padx=15, pady=12)
            card.grid(row=0, column=index, sticky="ew", padx=(0, 10 if index < 2 else 0))
            marker = tk.Label(
                card, text=" ", background=tint, width=1, height=2,
            )
            marker.pack(side="left", fill="y", padx=(0, 12))
            labels = tk.Frame(card, background=COLORS["surface"])
            labels.pack(side="left", fill="y")
            tk.Label(
                labels, text=label, background=COLORS["surface"], foreground=COLORS["muted"],
                font=("TkDefaultFont", 8, "bold"),
            ).pack(anchor="w")
            value = tk.Label(
                labels, text="0", background=COLORS["surface"], foreground=accent,
                font=("TkDefaultFont", 20, "bold"),
            )
            value.pack(anchor="w", pady=(2, 0))
            self.stat_values[key] = value
            stats.columnconfigure(index, weight=1)

    def _build_task_panel(self, parent: tk.Widget) -> None:
        panel = tk.Frame(parent, background=COLORS["surface"], highlightthickness=1,
                         highlightbackground=COLORS["line"])
        panel.pack(fill="both", expand=True)

        panel_heading = tk.Frame(panel, background=COLORS["surface"])
        panel_heading.pack(fill="x", padx=20, pady=(18, 13))
        tk.Label(
            panel_heading, text="Your tasks", background=COLORS["surface"],
            foreground=COLORS["ink"], font=("TkDefaultFont", 14, "bold"),
        ).pack(side="left")
        tk.Label(
            panel_heading, text="Plan it. Do it. Done.", background=COLORS["surface"],
            foreground=COLORS["muted"], font=("TkDefaultFont", 9),
        ).pack(side="right", pady=(3, 0))

        toolbar = tk.Frame(panel, background=COLORS["surface"])
        toolbar.pack(fill="x", padx=20, pady=(0, 12))
        tabs = tk.Frame(toolbar, background=COLORS["surface"])
        tabs.pack(side="left")
        for key, label in (("all", "All"), ("open", "To do"), ("completed", "Completed")):
            button = tk.Button(
                tabs, text=f"{label}  0", command=lambda selected=key: self.set_status(selected),
                relief="flat", bd=0, padx=9, pady=7, cursor="hand2",
                font=("TkDefaultFont", 9),
            )
            button.pack(side="left", padx=(0, 4))
            self.tab_buttons[key] = button

        search_wrap = tk.Frame(toolbar, background=COLORS["surface"], highlightthickness=1,
                               highlightbackground=COLORS["line"])
        search_wrap.pack(side="right", fill="x", expand=True, padx=(10, 0))
        search_wrap.configure(width=250)
        search_wrap.pack_propagate(False)
        tk.Label(
            search_wrap, text="⌕", background=COLORS["surface"], foreground=COLORS["muted"],
            font=("TkDefaultFont", 15),
        ).pack(side="left", padx=(9, 3))
        search = tk.Entry(
            search_wrap, textvariable=self.search_text, relief="flat", bd=0,
            background=COLORS["surface"], foreground=COLORS["ink"],
            insertbackground=COLORS["green"], font=("TkDefaultFont", 9),
        )
        search.pack(side="left", fill="both", expand=True, padx=(2, 6))
        search.bind("<KeyRelease>", lambda _event: self.refresh())
        priority = ttk.Combobox(
            toolbar, textvariable=self.priority_filter, values=("all", *PRIORITIES),
            state="readonly", width=12, style="Task.TCombobox",
        )
        priority.pack(side="right", padx=(8, 0))
        priority.bind("<<ComboboxSelected>>", lambda _event: self.refresh())

        divider = tk.Frame(panel, height=1, background=COLORS["line"])
        divider.pack(fill="x", padx=20)

        list_area = tk.Frame(panel, background=COLORS["surface"])
        list_area.pack(fill="both", expand=True, padx=(20, 13), pady=(3, 0))
        self.canvas = tk.Canvas(list_area, background=COLORS["surface"], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(list_area, orient="vertical", command=self.canvas.yview)
        self.rows = tk.Frame(self.canvas, background=COLORS["surface"])
        self.rows_window = self.canvas.create_window((0, 0), window=self.rows, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.rows.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_rows)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<MouseWheel>", self._scroll)

        footer = tk.Frame(panel, background=COLORS["surface"])
        footer.pack(fill="x", padx=20, pady=(9, 14))
        tk.Frame(footer, height=1, background=COLORS["line"]).pack(fill="x", pady=(0, 10))
        tk.Label(
            footer, text="One step at a time.", background=COLORS["surface"],
            foreground=COLORS["muted"], font=("TkDefaultFont", 8),
        ).pack(side="left")
        tk.Label(
            footer, textvariable=self.count_text, background=COLORS["surface"],
            foreground=COLORS["muted"], font=("TkDefaultFont", 8),
        ).pack(side="right")

    def _button(
        self, parent: tk.Widget, text: str, command: Any, *, primary: bool = False
    ) -> tk.Button:
        background = COLORS["green"] if primary else COLORS["surface"]
        foreground = "#ffffff" if primary else COLORS["ink"]
        active_background = COLORS["green_hover"] if primary else COLORS["green_soft"]
        return tk.Button(
            parent, text=text, command=command, relief="flat", bd=0, padx=13, pady=8,
            background=background, foreground=foreground, activebackground=active_background,
            activeforeground=foreground, cursor="hand2", font=("TkDefaultFont", 9, "bold"),
        )

    def _update_scroll_region(self, _event: Any = None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_rows(self, event: Any) -> None:
        self.canvas.itemconfigure(self.rows_window, width=event.width)

    def _scroll(self, event: Any) -> None:
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def set_status(self, status: str) -> None:
        self.status_filter.set(status)
        self.refresh()

    def refresh(self) -> None:
        try:
            status = self.status_filter.get()
            selected_priority = self.priority_filter.get()
            tasks = self.store.list_tasks(
                status=status,
                priority=None if selected_priority == "all" else selected_priority,
                search=self.search_text.get().strip() or None,
            )
            stats = self.store.stats()
            counts = {
                "all": stats["total"],
                "open": stats["open"],
                "completed": stats["completed"],
            }
        except (OSError, sqlite3.Error, ValueError) as error:
            self._show_error(error)
            return

        for key, value in stats.items():
            if key in self.stat_values:
                self.stat_values[key].configure(text=str(value))
        for key, button in self.tab_buttons.items():
            active = key == status
            label = {"all": "All", "open": "To do", "completed": "Completed"}[key]
            button.configure(
                text=f"{label}  {counts[key]}",
                background=COLORS["green_soft"] if active else COLORS["surface"],
                foreground=COLORS["green"] if active else COLORS["muted"],
                activebackground=COLORS["green_soft"],
                activeforeground=COLORS["green"],
                font=("TkDefaultFont", 9, "bold" if active else "normal"),
            )

        for child in self.rows.winfo_children():
            child.destroy()
        if not tasks:
            self._show_empty_state()
        else:
            for task in tasks:
                self._add_task_row(task)
        self.count_text.set(f"{len(tasks)} task{'s' if len(tasks) != 1 else ''}")
        self._update_scroll_region()

    def _show_empty_state(self) -> None:
        empty = tk.Frame(self.rows, background=COLORS["surface"], pady=54)
        empty.pack(fill="x")
        icon = tk.Label(
            empty, text="✓", background=COLORS["green_soft"], foreground=COLORS["green"],
            width=3, height=1, font=("TkDefaultFont", 15, "bold"),
        )
        icon.pack(pady=(0, 11), ipady=4)
        query_active = bool(self.search_text.get().strip()) or self.priority_filter.get() != "all"
        if query_active:
            title, detail = "No matching tasks", "Try changing your search or filters."
        elif self.status_filter.get() == "completed":
            title, detail = "Nothing completed yet", "Completed tasks will show up here."
        elif self.status_filter.get() == "open":
            title, detail = "You’re all caught up", "Add a task whenever something new comes up."
        else:
            title, detail = "Your list is looking fresh", "Add your first task and take it from there."
        tk.Label(
            empty, text=title, background=COLORS["surface"], foreground=COLORS["ink"],
            font=("TkDefaultFont", 11, "bold"),
        ).pack()
        tk.Label(
            empty, text=detail, background=COLORS["surface"], foreground=COLORS["muted"],
            font=("TkDefaultFont", 9),
        ).pack(pady=(5, 0))

    def _add_task_row(self, task: dict[str, Any]) -> None:
        today = date.today().isoformat()
        overdue = bool(task["due_date"] and task["due_date"] < today and not task["completed"])
        row = tk.Frame(self.rows, background=COLORS["surface"], pady=12)
        row.pack(fill="x")
        completed_var = tk.BooleanVar(value=bool(task["completed"]))
        check = tk.Checkbutton(
            row, command=lambda task_id=task["id"], value=not bool(task["completed"]):
                self._set_completed(task_id, value),
            variable=completed_var,
            background=COLORS["surface"], activebackground=COLORS["surface"],
            selectcolor=COLORS["green_soft"], fg=COLORS["green"],
            highlightthickness=0, bd=0, cursor="hand2",
        )
        check.task_variable = completed_var
        check.pack(side="left", anchor="n", padx=(1, 11))

        content = tk.Frame(row, background=COLORS["surface"])
        content.pack(side="left", fill="x", expand=True)
        title_color = COLORS["muted"] if task["completed"] else COLORS["ink"]
        title_font = ("TkDefaultFont", 10, "overstrike") if task["completed"] else ("TkDefaultFont", 10, "bold")
        tk.Label(
            content, text=task["title"], background=COLORS["surface"], foreground=title_color,
            font=title_font, anchor="w", justify="left", wraplength=540,
        ).pack(anchor="w", fill="x")
        meta = tk.Frame(content, background=COLORS["surface"])
        meta.pack(anchor="w", pady=(6, 0))

        priority_color, priority_tint = PRIORITY_COLORS[task["priority"]]
        tk.Label(
            meta, text=f"●  {task['priority'].title()}", background=priority_tint,
            foreground=priority_color, font=("TkDefaultFont", 8, "bold"), padx=7, pady=3,
        ).pack(side="left")
        if task["due_date"]:
            due_label = self._format_due_date(task["due_date"])
            due_color = COLORS["red"] if overdue else COLORS["muted"]
            due_tint = COLORS["red_soft"] if overdue else COLORS["background"]
            tk.Label(
                meta, text=f"{'Overdue · ' if overdue else 'Due '}{due_label}",
                background=due_tint, foreground=due_color,
                font=("TkDefaultFont", 8, "bold" if overdue else "normal"),
                padx=7, pady=3,
            ).pack(side="left", padx=(6, 0))
        if task["description"]:
            tk.Label(
                content, text=task["description"], background=COLORS["surface"],
                foreground=COLORS["muted"], font=("TkDefaultFont", 8),
                anchor="w", justify="left", wraplength=580,
            ).pack(anchor="w", pady=(6, 0))

        actions = tk.Frame(row, background=COLORS["surface"])
        actions.pack(side="right", anchor="n", padx=(8, 1))
        self._small_action(actions, "Edit", lambda task_id=task["id"]: self.edit_task(task_id)).pack(side="left")
        self._small_action(
            actions, "×", lambda task_id=task["id"], title=task["title"]: self.delete_task(task_id, title),
            danger=True,
        ).pack(side="left", padx=(4, 0))
        tk.Frame(self.rows, height=1, background=COLORS["line"]).pack(fill="x")

    @staticmethod
    def _format_due_date(value: str) -> str:
        due = date.fromisoformat(value)
        return due.strftime("%b %d").replace(" 0", " ")

    def _small_action(
        self, parent: tk.Widget, text: str, command: Any, *, danger: bool = False
    ) -> tk.Button:
        foreground = COLORS["red"] if danger else COLORS["muted"]
        return tk.Button(
            parent, text=text, command=command, relief="flat", bd=0, padx=8, pady=4,
            background=COLORS["surface"], foreground=foreground,
            activebackground=COLORS["red_soft"] if danger else COLORS["green_soft"],
            activeforeground=foreground, cursor="hand2", font=("TkDefaultFont", 8),
        )

    def add_task(self) -> None:
        self._open_task_dialog()

    def edit_task(self, task_id: int) -> None:
        try:
            task = self.store.get(task_id)
        except (TaskNotFoundError, OSError, sqlite3.Error) as error:
            self._show_error(error)
            self.refresh()
            return
        self._open_task_dialog(task)

    def _open_task_dialog(self, task: dict[str, Any] | None = None) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit task" if task else "New task")
        dialog.configure(background=COLORS["background"])
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.grab_set()

        frame = tk.Frame(dialog, background=COLORS["background"], padx=22, pady=20)
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame, text="Edit task" if task else "Create a task",
            background=COLORS["background"], foreground=COLORS["ink"],
            font=("TkDefaultFont", 15, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        title_var = tk.StringVar(value=task["title"] if task else "")
        priority_var = tk.StringVar(value=task["priority"] if task else "medium")
        due_var = tk.StringVar(value=(task["due_date"] or "") if task else "")
        tk.Label(
            frame, text="Task name", background=COLORS["background"],
            foreground=COLORS["ink"], font=("TkDefaultFont", 9, "bold"),
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 5))
        title_entry = tk.Entry(
            frame, textvariable=title_var, width=48, relief="flat", bd=0,
            background=COLORS["surface"], foreground=COLORS["ink"],
            insertbackground=COLORS["green"], highlightthickness=1,
            highlightbackground=COLORS["line"], highlightcolor=COLORS["green"],
            font=("TkDefaultFont", 10),
        )
        title_entry.grid(row=2, column=0, columnspan=2, sticky="ew", ipady=8, padx=1)
        tk.Label(
            frame, text="Description (optional)", background=COLORS["background"],
            foreground=COLORS["ink"], font=("TkDefaultFont", 9, "bold"),
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(12, 5))
        description = tk.Text(
            frame, width=48, height=4, wrap="word", relief="flat", bd=0,
            background=COLORS["surface"], foreground=COLORS["ink"],
            insertbackground=COLORS["green"], highlightthickness=1,
            highlightbackground=COLORS["line"], highlightcolor=COLORS["green"],
            font=("TkDefaultFont", 10),
        )
        description.grid(row=4, column=0, columnspan=2, sticky="ew", padx=1)
        if task:
            description.insert("1.0", task["description"])

        tk.Label(
            frame, text="Priority", background=COLORS["background"],
            foreground=COLORS["ink"], font=("TkDefaultFont", 9, "bold"),
        ).grid(row=5, column=0, sticky="w", pady=(12, 5))
        tk.Label(
            frame, text="Due date (YYYY-MM-DD)", background=COLORS["background"],
            foreground=COLORS["ink"], font=("TkDefaultFont", 9, "bold"),
        ).grid(row=5, column=1, sticky="w", padx=(12, 0), pady=(12, 5))
        ttk.Combobox(
            frame, textvariable=priority_var, values=PRIORITIES, state="readonly",
            width=16, style="Task.TCombobox",
        ).grid(row=6, column=0, sticky="ew")
        tk.Entry(
            frame, textvariable=due_var, width=24, relief="flat", bd=0,
            background=COLORS["surface"], foreground=COLORS["ink"],
            insertbackground=COLORS["green"], highlightthickness=1,
            highlightbackground=COLORS["line"], highlightcolor=COLORS["green"],
            font=("TkDefaultFont", 10),
        ).grid(row=6, column=1, sticky="ew", padx=(12, 1), ipady=8)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        buttons = tk.Frame(frame, background=COLORS["background"])
        buttons.grid(row=7, column=0, columnspan=2, sticky="e", pady=(18, 0))
        tk.Button(
            buttons, text="Cancel", command=dialog.destroy, relief="flat", bd=0,
            padx=12, pady=8, background=COLORS["background"], foreground=COLORS["muted"],
            activebackground=COLORS["line"], cursor="hand2", font=("TkDefaultFont", 9),
        ).pack(side="right", padx=(7, 0))

        def save() -> None:
            try:
                title = validate_title(title_var.get())
                task_description = description.get("1.0", "end-1c").strip()
                priority = priority_var.get()
                due_date = due_var.get().strip() or None
                if task:
                    self.store.update(
                        task["id"],
                        {
                            "title": title,
                            "description": task_description,
                            "priority": priority,
                            "due_date": due_date,
                        },
                    )
                else:
                    self.store.add(title, task_description, priority, due_date)
            except (ValueError, TaskNotFoundError, OSError, sqlite3.Error) as error:
                self._show_error(error, parent=dialog)
                return
            dialog.destroy()
            self.refresh()

        tk.Button(
            buttons, text="Save task", command=save, relief="flat", bd=0,
            padx=14, pady=8, background=COLORS["green"], foreground="white",
            activebackground=COLORS["green_hover"], activeforeground="white",
            cursor="hand2", font=("TkDefaultFont", 9, "bold"),
        ).pack(side="right")
        title_entry.focus_set()
        dialog.bind("<Return>", lambda _event: save())
        self.root.wait_window(dialog)

    def _set_completed(self, task_id: int, completed: bool) -> None:
        try:
            self.store.set_completed(task_id, completed)
        except (TaskNotFoundError, OSError, sqlite3.Error) as error:
            self._show_error(error)
        self.refresh()

    def delete_task(self, task_id: int, title: str) -> None:
        if not messagebox.askyesno("Delete task", f'Delete "{title}"?', parent=self.root):
            return
        try:
            self.store.delete(task_id)
        except (TaskNotFoundError, OSError, sqlite3.Error) as error:
            self._show_error(error)
        self.refresh()

    def _show_error(self, error: Exception, parent: tk.Misc | None = None) -> None:
        messagebox.showerror("TaskTracker", str(error), parent=parent or self.root)


def launch(store: TaskStore) -> None:
    root = tk.Tk()
    TaskTrackerWindow(root, store)
    root.mainloop()
