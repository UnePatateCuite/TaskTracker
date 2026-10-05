# TaskTracker

A small, dependency-free task tracker that runs entirely in your browser. Your tasks are saved in this browser's local storage; nothing is sent to a server.

## Run locally

Open `index.html` in a modern browser. You can also serve the folder locally:

```sh
python3 -m http.server 8000
```

Then open [http://localhost:8000](http://localhost:8000).

## Features

- Create tasks with a description, priority, and optional due date
- Edit, complete, and delete tasks
- Search tasks and filter by status or priority
- See a summary of open, completed, and overdue tasks
- Automatically save changes in browser local storage

Tasks are stored separately for each browser and device. Clearing this site's browser data will remove saved tasks.