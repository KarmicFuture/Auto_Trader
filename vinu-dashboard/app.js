"use strict";

const path = require("path");
const express = require("express");
const { createApiRouter } = require("./server");

const app = express();
const PORT = process.env.PORT || 3000;

app.disable("x-powered-by");
app.use(express.json({ limit: "256kb" }));
app.use(express.static(path.join(__dirname, "public")));

app.get("/health", (_req, res) => {
  res.json({
    ok: true,
    service: "vinu-dashboard",
    site: "https://vinu.us",
    time: new Date().toISOString(),
  });
});

app.use("/api", createApiRouter());

app.get("*", (_req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`Vinu Dashboard listening on http://0.0.0.0:${PORT}`);
});
