# TaskTracker

A local desktop task tracker with an optional command-line interface. It runs with Python 3.10 or newer and uses SQLite to save tasks on your computer. The desktop app is a native window; it does not open a browser or run a web server.

## Run

On Ubuntu or Debian, install Tkinter once if it is not already available:

```sh
sudo apt install python3-tk
```

From the project folder, launch the desktop app:

```sh
python3 tasktracker.py
```

In the task editor, choose **Today** for the current date or use the calendar button to pick a date. In the calendar, use the month and year dropdowns to jump directly to a date, or the arrows to move one month at a time.

## Linux Mint Cinnamon desktop desklet

The optional Cinnamon desklet sits directly on your desktop. It shows your open tasks and count, supports quick add and one-click completion, and opens the full TaskTracker window. It uses the same local SQLite database as the desktop app and CLI.

Right-click the desklet and choose **Configure…** to adjust background opacity (transparent to opaque) and corner roundness (square to rounded). Changes apply immediately.

Install the desklet:

```sh
bash install-cinnamon-desklet.sh
```

Then open **System Settings → Desklets → Installed**, select **TaskTracker**, and choose **Add to desktop**. If it does not appear in the list, restart Cinnamon with **Alt+F2**, type `r`, and press Enter. Python 3 must be available on `PATH`. The installer removes the earlier TaskTracker panel-applet files from your user applet folder.

To use the command-line interface instead:

```sh
python3 tasktracker.py --help
```

## Commands

```sh
python3 tasktracker.py add "Prepare project proposal" --priority high --due 2026-10-20 --description "Draft the outline"
python3 tasktracker.py list
python3 tasktracker.py list --status open --priority high --search proposal
python3 tasktracker.py show 1
python3 tasktracker.py edit 1 --title "Finish project proposal" --due 2026-10-22
python3 tasktracker.py complete 1
python3 tasktracker.py reopen 1
python3 tasktracker.py stats
python3 tasktracker.py delete 1
```

Task IDs are shown by `add` and `list`. Deleting a task asks for confirmation; use `--yes` to skip it.

Tasks created in the desktop app or command line are saved in `~/.tasktracker/tasks.sqlite3` by default. Set `TASKTRACKER_DB` to choose a different database file. The database stays on your computer and can be backed up by copying that file.

Run the tests with:

```sh
python3 -m unittest
```
