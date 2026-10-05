const Desklet = imports.ui.desklet;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Mainloop = imports.mainloop;
const St = imports.gi.St;
const Main = imports.ui.main;

const MAX_VISIBLE_TASKS = 6;
const REFRESH_SECONDS = 30;
const COLORS = {
    background: "#ffffff",
    ink: "#202b27",
    muted: "#818d87",
    line: "#e8edea",
    green: "#28785d",
    greenSoft: "#eaf3ee",
    red: "#b9554d",
    redSoft: "#fbefed",
    amber: "#98702f",
    amberSoft: "#f8f2e7"
};

class TaskTrackerDesklet extends Desklet.Desklet {
    constructor(metadata, deskletId) {
        super(metadata, deskletId);
        this.metadata = metadata;
        this.bridgePath = GLib.build_filenamev([metadata.path, "tasktracker_desklet_bridge.py"]);
        this.tasktrackerPath = GLib.build_filenamev([metadata.path, "tasktracker.py"]);
        this.requestId = 0;
        this.refreshSourceId = 0;
        this.setHeader("TaskTracker");
        this._buildContent();
        this._refresh();
        this.refreshSourceId = Mainloop.timeout_add_seconds(REFRESH_SECONDS, () => {
            this._refresh();
            return true;
        });
    }

    _buildContent() {
        this.container = new St.BoxLayout({
            vertical: true,
            style: "width: 340px; padding: 16px; spacing: 10px;" +
                `background-color: ${COLORS.background}; border: 1px solid ${COLORS.line};` +
                "border-radius: 18px;"
        });

        const heading = new St.BoxLayout({ vertical: false, style: "spacing: 8px;" });
        const title = new St.Label({
            text: "Your tasks",
            style: `font-size: 15px; font-weight: bold; color: ${COLORS.ink};`
        });
        heading.add_child(title);
        this.countLabel = new St.Label({
            text: "…",
            style: `font-size: 11px; color: ${COLORS.muted};`
        });
        heading.add_child(this.countLabel);
        this.container.add_child(heading);

        this.messageLabel = new St.Label({
            text: "Loading your tasks…",
            style: `font-size: 11px; color: ${COLORS.muted};`
        });
        this.container.add_child(this.messageLabel);

        this.taskList = new St.BoxLayout({ vertical: true, style: "spacing: 5px;" });
        this.container.add_child(this.taskList);

        const addRow = new St.BoxLayout({ vertical: false, style: "spacing: 6px;" });
        this.addEntry = new St.Entry({
            hint_text: "Add a task…",
            can_focus: true,
            style: `min-width: 220px; padding: 8px; border-radius: 10px;` +
                `background-color: ${COLORS.background}; color: ${COLORS.ink};`
        });
        this.addEntry.clutter_text.connect("activate", () => this._addTask());
        addRow.add_child(this.addEntry);
        this.addButton = new St.Button({
            label: "Add",
            can_focus: true,
            style: `padding: 7px 11px; border-radius: 10px;` +
                `background-color: ${COLORS.greenSoft}; color: ${COLORS.green}; font-weight: bold;`
        });
        this.addButton.connect("clicked", () => this._addTask());
        addRow.add_child(this.addButton);
        this.container.add_child(addRow);

        const openApp = new St.Button({
            label: "Open full TaskTracker",
            can_focus: true,
            style: `padding: 7px; border-radius: 10px; color: ${COLORS.muted};`
        });
        openApp.connect("clicked", () => this._openDesktopApp());
        this.container.add_child(openApp);
        this.setContent(this.container);
    }

    _runBridge(args, callback) {
        let process;
        try {
            process = Gio.Subprocess.new(
                ["python3", this.bridgePath, ...args],
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE
            );
        } catch (error) {
            callback(null, error.message);
            return;
        }
        process.communicate_utf8_async(null, null, (source, result) => {
            try {
                const [, stdout, stderr] = source.communicate_utf8_finish(result);
                if (source.get_exit_status() !== 0) {
                    callback(null, (stderr || "TaskTracker could not complete that action.").trim());
                    return;
                }
                callback(JSON.parse(stdout), null);
            } catch (error) {
                callback(null, error.message);
            }
        });
    }

    _refresh() {
        const requestId = ++this.requestId;
        this._runBridge(["list"], (result, error) => {
            if (requestId !== this.requestId) {
                return;
            }
            if (error) {
                this.countLabel.set_text("!");
                this.messageLabel.set_text(`Could not load tasks: ${error}`);
                return;
            }
            this._renderTasks(result.tasks, result.open_count);
        });
    }

    _renderTasks(tasks, openCount) {
        this.countLabel.set_text(`${openCount} to do`);
        this.messageLabel.set_text(openCount === 0 ? "You’re all caught up." : "Click a task to mark it done.");
        for (const child of this.taskList.get_children()) {
            this.taskList.remove_child(child);
        }

        for (const task of tasks.slice(0, MAX_VISIBLE_TASKS)) {
            this.taskList.add_child(this._createTaskRow(task));
        }
        if (tasks.length > MAX_VISIBLE_TASKS) {
            this.taskList.add_child(new St.Label({
                text: `${tasks.length - MAX_VISIBLE_TASKS} more tasks…`,
                style: `padding: 4px; color: ${COLORS.muted}; font-size: 10px;`
            }));
        }
    }

    _createTaskRow(task) {
        const due = task.due_date ? ` · ${task.due_date}` : "";
        const priorityColor = task.priority === "high" ? COLORS.red :
            task.priority === "medium" ? COLORS.amber : COLORS.green;
        const row = new St.Button({
            can_focus: true,
            reactive: true,
            style: `padding: 9px 10px; border-radius: 12px;` +
                `background-color: ${COLORS.background}; color: ${COLORS.ink};`
        });
        const contents = new St.BoxLayout({ vertical: true, style: "spacing: 3px;" });
        contents.add_child(new St.Label({
            text: `○  ${task.title}`,
            style: `font-size: 11px; color: ${COLORS.ink};`
        }));
        contents.add_child(new St.Label({
            text: `${task.priority.toUpperCase()}${due}`,
            style: `font-size: 9px; color: ${priorityColor};`
        }));
        row.set_child(contents);
        row.connect("clicked", () => this._completeTask(task.id));
        return row;
    }

    _addTask() {
        const title = this.addEntry.get_text().trim();
        if (!title) {
            this.addEntry.grab_key_focus();
            return;
        }
        const requestId = ++this.requestId;
        this.addButton.set_label("Saving…");
        this.addButton.set_reactive(false);
        this._runBridge(["add", title], (result, error) => {
            this.addButton.set_label("Add");
            this.addButton.set_reactive(true);
            if (error) {
                Main.notifyError("TaskTracker", error);
                return;
            }
            this.addEntry.set_text("");
            if (requestId === this.requestId) {
                this._refresh();
            }
        });
    }

    _completeTask(taskId) {
        const requestId = ++this.requestId;
        this._runBridge(["complete", String(taskId)], (result, error) => {
            if (error) {
                Main.notifyError("TaskTracker", error);
                return;
            }
            if (requestId === this.requestId) {
                this._refresh();
            }
        });
    }

    _openDesktopApp() {
        try {
            Gio.Subprocess.new(["python3", this.tasktrackerPath], Gio.SubprocessFlags.NONE);
        } catch (error) {
            Main.notifyError("TaskTracker", error.message);
        }
    }

    on_desklet_removed() {
        this.requestId++;
        if (this.refreshSourceId) {
            Mainloop.source_remove(this.refreshSourceId);
            this.refreshSourceId = 0;
        }
    }
}

function main(metadata, deskletId) {
    return new TaskTrackerDesklet(metadata, deskletId);
}
