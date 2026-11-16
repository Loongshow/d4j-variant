import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const appRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const env = {
  ...process.env,
  D4J_API_PORT: process.env.D4J_API_PORT ?? "8787",
  D4J_WEB_PORT: process.env.D4J_WEB_PORT ?? "5173",
};
const pnpmCommand = process.platform === "win32" ? "pnpm.cmd" : "pnpm";

const processes = [
  spawn(process.execPath, ["--watch", "--watch-path=server", "--watch-preserve-output", "server/index.mjs"], {
    cwd: appRoot,
    env,
    stdio: "inherit",
  }),
  spawn(pnpmCommand, ["run", "dev:web"], {
    cwd: appRoot,
    env,
    stdio: "inherit",
  }),
];

let stopping = false;

function stopAll(signal = "SIGTERM") {
  stopping = true;
  for (const child of processes) {
    if (!child.killed) {
      child.kill(signal);
    }
  }
}

for (const child of processes) {
  child.on("exit", (code) => {
    if (stopping) return;
    if (code && code !== 0) {
      stopAll();
      process.exit(code);
    }
  });
}

process.on("SIGINT", () => {
  stopAll("SIGINT");
  process.exit(0);
});

process.on("SIGTERM", () => {
  stopAll("SIGTERM");
  process.exit(0);
});
