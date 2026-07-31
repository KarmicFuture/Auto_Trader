import { cpSync, mkdirSync, rmSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const dist = join(root, "dist");

rmSync(dist, { recursive: true, force: true });
mkdirSync(dist, { recursive: true });

for (const entry of ["app.js", "server.js", "package.json", "public", "data"]) {
  cpSync(join(root, entry), join(dist, entry), { recursive: true });
}

console.log("Build complete → dist/");
