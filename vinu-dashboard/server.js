"use strict";

const fs = require("fs");
const path = require("path");
const express = require("express");

const DATA_DIR = path.join(__dirname, "data");
const STATE_FILE = path.join(DATA_DIR, "dashboard-state.json");

function readState() {
  const raw = fs.readFileSync(STATE_FILE, "utf8");
  return JSON.parse(raw);
}

function writeState(state) {
  fs.writeFileSync(STATE_FILE, `${JSON.stringify(state, null, 2)}\n`, "utf8");
}

function createApiRouter() {
  const router = express.Router();

  router.get("/overview", (_req, res) => {
    const state = readState();
    const done = state.checklist.filter((item) => item.done).length;
    res.json({
      brand: state.brand,
      siteUrl: state.siteUrl,
      status: state.status,
      tagline: state.tagline,
      checklistProgress: {
        done,
        total: state.checklist.length,
        percent: Math.round((done / state.checklist.length) * 100),
      },
      pageCount: state.pages.length,
      projectCount: state.projects.length,
      openTasks: state.tasks.filter((task) => !task.done).length,
      updatedAt: state.updatedAt,
    });
  });

  router.get("/pages", (_req, res) => {
    res.json(readState().pages);
  });

  router.get("/projects", (_req, res) => {
    res.json(readState().projects);
  });

  router.get("/checklist", (_req, res) => {
    res.json(readState().checklist);
  });

  router.patch("/checklist/:id", (req, res) => {
    const state = readState();
    const item = state.checklist.find((entry) => entry.id === req.params.id);
    if (!item) {
      return res.status(404).json({ error: "Checklist item not found" });
    }
    if (typeof req.body.done === "boolean") {
      item.done = req.body.done;
    }
    state.updatedAt = new Date().toISOString();
    writeState(state);
    return res.json(item);
  });

  router.get("/tasks", (_req, res) => {
    res.json(readState().tasks);
  });

  router.post("/tasks", (req, res) => {
    const title = String(req.body.title || "").trim();
    if (!title) {
      return res.status(400).json({ error: "Task title is required" });
    }
    const state = readState();
    const task = {
      id: `task-${Date.now()}`,
      title,
      done: false,
      createdAt: new Date().toISOString(),
    };
    state.tasks.unshift(task);
    state.updatedAt = new Date().toISOString();
    writeState(state);
    return res.status(201).json(task);
  });

  router.patch("/tasks/:id", (req, res) => {
    const state = readState();
    const task = state.tasks.find((entry) => entry.id === req.params.id);
    if (!task) {
      return res.status(404).json({ error: "Task not found" });
    }
    if (typeof req.body.done === "boolean") {
      task.done = req.body.done;
    }
    if (typeof req.body.title === "string" && req.body.title.trim()) {
      task.title = req.body.title.trim();
    }
    state.updatedAt = new Date().toISOString();
    writeState(state);
    return res.json(task);
  });

  router.delete("/tasks/:id", (req, res) => {
    const state = readState();
    const before = state.tasks.length;
    state.tasks = state.tasks.filter((entry) => entry.id !== req.params.id);
    if (state.tasks.length === before) {
      return res.status(404).json({ error: "Task not found" });
    }
    state.updatedAt = new Date().toISOString();
    writeState(state);
    return res.status(204).end();
  });

  router.get("/activity", (_req, res) => {
    res.json(readState().activity);
  });

  return router;
}

module.exports = { createApiRouter, readState, writeState };
