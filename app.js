"use strict";

const STORAGE_KEY = "tasktracker.tasks.v1";
const PRIORITIES = ["low", "medium", "high"];
const elements = {
  form: document.querySelector("#task-form"),
  formTitle: document.querySelector("#form-title"),
  title: document.querySelector("#task-name"),
  description: document.querySelector("#task-description"),
  priority: document.querySelector("#task-priority"),
  dueDate: document.querySelector("#task-due"),
  list: document.querySelector("#task-list"),
  search: document.querySelector("#search-input"),
  priorityFilter: document.querySelector("#priority-filter"),
  summary: document.querySelector("#list-summary")
};

let tasks = loadTasks();
let activeStatus = "all";
let editingId = null;

function loadTasks() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    const parsed = JSON.parse(stored);
    if (!Array.isArray(parsed)) throw new Error("Saved task data is not a list.");
    return parsed.filter((task) =>
      task &&
      typeof task.id === "string" &&
      typeof task.title === "string" &&
      typeof task.completed === "boolean" &&
      PRIORITIES.includes(task.priority)
    );
  } catch (error) {
    console.error("Could not load saved tasks:", error);
    return [];
  }
}

function saveTasks() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
  } catch (error) {
    console.error("Could not save tasks to local storage:", error);
    window.alert("Your changes could not be saved in this browser. Check available storage and try again.");
  }
}

function makeElement(tagName, className, text) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function formatDate(value) {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function isOverdue(task) {
  return Boolean(task.dueDate && !task.completed && task.dueDate < new Date().toLocaleDateString("en-CA"));
}

function createTaskCard(task) {
  const card = makeElement("article", `task-card${task.completed ? " completed" : ""}`);
  const checkbox = makeElement("input", "task-check");
  checkbox.type = "checkbox";
  checkbox.checked = task.completed;
  checkbox.setAttribute("aria-label", `${task.completed ? "Mark as to do" : "Complete"}: ${task.title}`);
  checkbox.addEventListener("change", () => {
    task.completed = checkbox.checked;
    saveTasks();
    render();
  });

  const content = makeElement("div", "task-content");
  content.append(makeElement("h3", "task-title", task.title));
  if (task.description) content.append(makeElement("p", "task-description", task.description));
  const meta = makeElement("div", "task-meta");
  meta.append(makeElement("span", `priority priority-${task.priority}`, `${task.priority[0].toUpperCase()}${task.priority.slice(1)} priority`));
  if (task.dueDate) {
    const dueDate = makeElement("span", `due-date${isOverdue(task) ? " overdue" : ""}`, `${isOverdue(task) ? "Overdue · " : "Due "}${formatDate(task.dueDate)}`);
    meta.append(dueDate);
  }
  content.append(meta);

  const actions = makeElement("div", "task-actions");
  const editButton = makeElement("button", "icon-button", "✎");
  editButton.type = "button";
  editButton.setAttribute("aria-label", `Edit ${task.title}`);
  editButton.addEventListener("click", () => openForm(task));
  const deleteButton = makeElement("button", "icon-button", "×");
  deleteButton.type = "button";
  deleteButton.setAttribute("aria-label", `Delete ${task.title}`);
  deleteButton.addEventListener("click", () => {
    if (!window.confirm(`Delete "${task.title}"?`)) return;
    tasks = tasks.filter((item) => item.id !== task.id);
    saveTasks();
    render();
  });
  actions.append(editButton, deleteButton);
  card.append(checkbox, content, actions);
  return card;
}

function render() {
  const openCount = tasks.filter((task) => !task.completed).length;
  const completedCount = tasks.length - openCount;
  const overdueCount = tasks.filter(isOverdue).length;
  document.querySelector("#open-count").textContent = openCount;
  document.querySelector("#completed-count").textContent = completedCount;
  document.querySelector("#overdue-count").textContent = overdueCount;
  document.querySelector("#all-tab-count").textContent = tasks.length;
  document.querySelector("#todo-tab-count").textContent = openCount;
  document.querySelector("#done-tab-count").textContent = completedCount;

  const query = elements.search.value.trim().toLocaleLowerCase();
  const priority = elements.priorityFilter.value;
  const visibleTasks = tasks
    .filter((task) => activeStatus === "all" || (activeStatus === "completed" ? task.completed : !task.completed))
    .filter((task) => priority === "all" || task.priority === priority)
    .filter((task) => !query || `${task.title} ${task.description || ""}`.toLocaleLowerCase().includes(query))
    .sort((a, b) => Number(a.completed) - Number(b.completed) || (a.dueDate || "9999-12-31").localeCompare(b.dueDate || "9999-12-31") || b.createdAt - a.createdAt);

  elements.list.replaceChildren();
  if (!visibleTasks.length) {
    const empty = makeElement("div", "empty-state");
    empty.append(makeElement("span", "empty-icon", query || priority !== "all" ? "⌕" : "✓"));
    empty.append(makeElement("h3", "", query || priority !== "all" ? "No matching tasks" : tasks.length ? "Nothing to show here" : "Your list is looking fresh"));
    empty.append(makeElement("p", "", query || priority !== "all" ? "Try changing your search or filters." : tasks.length ? "Try another filter, or add a task to get started." : "Add a task and take the first step."));
    elements.list.append(empty);
  } else {
    visibleTasks.forEach((task) => elements.list.append(createTaskCard(task)));
  }
  elements.summary.textContent = `${visibleTasks.length} ${visibleTasks.length === 1 ? "task" : "tasks"}`;
}

function openForm(task = null) {
  editingId = task ? task.id : null;
  elements.formTitle.textContent = task ? "Edit task" : "Add a task";
  document.querySelector("#save-task").textContent = task ? "Save changes" : "Save task";
  elements.title.value = task?.title || "";
  elements.description.value = task?.description || "";
  elements.priority.value = task?.priority || "medium";
  elements.dueDate.value = task?.dueDate || "";
  elements.form.hidden = false;
  elements.title.focus();
  elements.form.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function closeForm() {
  elements.form.reset();
  elements.form.hidden = true;
  editingId = null;
}

elements.form.addEventListener("submit", (event) => {
  event.preventDefault();
  const title = elements.title.value.trim();
  if (!title) {
    elements.title.focus();
    return;
  }
  const values = {
    title,
    description: elements.description.value.trim(),
    priority: elements.priority.value,
    dueDate: elements.dueDate.value
  };
  if (editingId) {
    tasks = tasks.map((task) => task.id === editingId ? { ...task, ...values } : task);
  } else {
    tasks.push({ id: crypto.randomUUID(), ...values, completed: false, createdAt: Date.now() });
  }
  saveTasks();
  closeForm();
  render();
});

document.querySelector("#add-task-button").addEventListener("click", () => openForm());
document.querySelector("#close-form").addEventListener("click", closeForm);
document.querySelector("#cancel-form").addEventListener("click", closeForm);
document.querySelectorAll(".filter-button").forEach((button) => {
  button.addEventListener("click", () => {
    activeStatus = button.dataset.status;
    document.querySelectorAll(".filter-button").forEach((item) => item.classList.toggle("active", item === button));
    render();
  });
});
elements.search.addEventListener("input", render);
elements.priorityFilter.addEventListener("change", render);
document.querySelector("#today-date").textContent = new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });
render();
