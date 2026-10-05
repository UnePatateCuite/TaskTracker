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
