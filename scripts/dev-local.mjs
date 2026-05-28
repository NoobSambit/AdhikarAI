#!/usr/bin/env node

import { spawn } from "node:child_process";
import { existsSync, mkdirSync } from "node:fs";
import { createInterface } from "node:readline";

const repoRoot = new URL("..", import.meta.url).pathname.replace(/\/$/, "");
const backendDir = `${repoRoot}/backend`;
const frontendDir = `${repoRoot}/frontend`;
const noSeed = process.argv.includes("--no-seed");

const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000",
  frontendHost: process.env.FRONTEND_HOST ?? "127.0.0.1",
  frontendPort: process.env.FRONTEND_PORT ?? "3000",
  backendHost: process.env.BACKEND_HOST ?? "127.0.0.1",
  backendPort: process.env.BACKEND_PORT ?? "8000",
  postgresDataDir: process.env.POSTGRES_DATA_DIR ?? "/home/noobsambit/.agent-playground/postgres/data",
  postgresLog: process.env.POSTGRES_LOG ?? "/home/noobsambit/.agent-playground/postgres/postgres.log",
  postgresSocketDir: process.env.POSTGRES_SOCKET_DIR ?? "/home/noobsambit/.agent-playground/postgres/socket",
  redisUrl: process.env.REDIS_URL ?? "redis://localhost:6379/0",
  dashboardCode: process.env.DASHBOARD_DEV_LOGIN_CODE ?? "local-e2e-login",
  cookieDir: process.env.E2E_COOKIE_DIR ?? "/tmp/adhikarai-local-e2e",
  uvCacheDir: process.env.UV_CACHE_DIR ?? "/tmp/uv-cache"
};

const children = new Map();

function timestamp() {
  return new Date().toLocaleTimeString("en-IN", { hour12: false });
}

function log(service, message) {
  process.stdout.write(`[${timestamp()}] [${service}] ${message}\n`);
}

function prefixStream(service, stream) {
  const reader = createInterface({ input: stream });
  reader.on("line", (line) => log(service, line));
}

function run(name, command, args, options = {}) {
  return new Promise((resolve, reject) => {
    log(name, `$ ${command} ${args.join(" ")}`);
    const child = spawn(command, args, {
      cwd: options.cwd ?? repoRoot,
      env: { ...process.env, ...(options.env ?? {}) },
      stdio: ["ignore", "pipe", "pipe"]
    });
    prefixStream(name, child.stdout);
    prefixStream(name, child.stderr);
    child.on("error", reject);
    child.on("exit", (code, signal) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`${name} exited with ${signal ?? code}`));
      }
    });
  });
}

function start(name, command, args, options = {}) {
  log(name, `$ ${command} ${args.join(" ")}`);
  const child = spawn(command, args, {
    cwd: options.cwd ?? repoRoot,
    env: { ...process.env, ...(options.env ?? {}) },
    stdio: ["ignore", "pipe", "pipe"]
  });
  children.set(name, child);
  prefixStream(name, child.stdout);
  prefixStream(name, child.stderr);
  child.on("exit", (code, signal) => {
    children.delete(name);
    log(name, `stopped (${signal ?? code})`);
    if (!shuttingDown && code !== 0) {
      log("local-dev", `${name} exited unexpectedly; shutting down remaining services.`);
      shutdown(1);
    }
  });
  return child;
}

async function commandOk(name, command, args, options = {}) {
  try {
    await run(name, command, args, options);
    return true;
  } catch {
    return false;
  }
}

async function waitFor(name, check, timeoutMs = 30_000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    if (await check()) {
      log(name, "ready");
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error(`${name} did not become ready within ${timeoutMs}ms`);
}

async function ensurePostgres() {
  log("postgres", `checking localhost:5432`);
  if (await commandOk("postgres", "pg_isready", ["-h", "localhost", "-p", "5432"])) {
    return;
  }
  if (!existsSync(config.postgresDataDir)) {
    throw new Error(`PostgreSQL data dir not found: ${config.postgresDataDir}`);
  }
  mkdirSync(config.postgresSocketDir, { recursive: true });
  await run("postgres", "pg_ctl", [
    "-D",
    config.postgresDataDir,
    "-l",
    config.postgresLog,
    "-o",
    `-h localhost -p 5432 -k ${config.postgresSocketDir}`,
    "start"
  ]);
  await waitFor("postgres", () => commandOk("postgres", "pg_isready", ["-h", "localhost", "-p", "5432"]));
}

async function ensureRedis() {
  log("redis", `checking ${config.redisUrl}`);
  if (await commandOk("redis", "redis-cli", ["-u", config.redisUrl, "ping"])) {
    return;
  }
  start("redis", "redis-server", ["--bind", "127.0.0.1", "--port", "6379", "--dir", "/tmp", "--dbfilename", "adhikarai-redis.rdb"]);
  await waitFor("redis", () => commandOk("redis", "redis-cli", ["-u", config.redisUrl, "ping"]));
}

async function migrateAndSeed() {
  const env = {
    UV_CACHE_DIR: config.uvCacheDir,
    APP_ENV: "local",
    LOCAL_E2E_HELPERS_ENABLED: "true",
    REDIS_URL: config.redisUrl
  };
  await run("migrate", "uv", ["run", "--extra", "test", "alembic", "upgrade", "head"], { cwd: backendDir, env });
  if (!noSeed) {
    await run("seed", "uv", ["run", "--extra", "test", "python", "-m", "app.cli.local_e2e", "--cookie-dir", config.cookieDir], {
      cwd: backendDir,
      env
    });
  } else {
    log("seed", "skipped because --no-seed was provided");
  }
}

async function waitForHttp(name, url) {
  await waitFor(name, async () => {
    try {
      const response = await fetch(url);
      return response.ok;
    } catch {
      return false;
    }
  }, 60_000);
}

let shuttingDown = false;

function shutdown(code = 0) {
  if (shuttingDown) return;
  shuttingDown = true;
  log("local-dev", "shutting down managed app services");
  for (const [name, child] of children) {
    log(name, "sending SIGINT");
    child.kill("SIGINT");
  }
  setTimeout(() => process.exit(code), 1200).unref();
}

process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));

async function main() {
  log("local-dev", "AdhikarAI local stack starting");
  log("local-dev", `frontend: http://${config.frontendHost}:${config.frontendPort}`);
  log("local-dev", `backend:  http://${config.backendHost}:${config.backendPort}`);
  log("local-dev", `redis:    ${config.redisUrl}`);
  log("local-dev", `seed:     ${noSeed ? "disabled" : config.cookieDir}`);

  await ensurePostgres();
  await ensureRedis();
  await migrateAndSeed();

  const backendEnv = {
    UV_CACHE_DIR: config.uvCacheDir,
    APP_ENV: "local",
    ENABLE_SCHEDULER: "false",
    AUTH_COOKIE_SECURE: "false",
    REDIS_URL: config.redisUrl,
    DASHBOARD_AUTH_PROVIDER: "dev",
    DASHBOARD_DEV_LOGIN_ENABLED: "true",
    DASHBOARD_DEV_LOGIN_CODE: config.dashboardCode,
    LOCAL_E2E_HELPERS_ENABLED: "true"
  };
  start("backend", "uv", ["run", "--extra", "test", "uvicorn", "app.main:app", "--host", config.backendHost, "--port", config.backendPort], {
    cwd: backendDir,
    env: backendEnv
  });
  await waitForHttp("backend", `http://${config.backendHost}:${config.backendPort}/health`);

  start("frontend", "npm", ["run", "dev", "--", "--hostname", config.frontendHost, "--port", config.frontendPort], {
    cwd: frontendDir,
    env: {
      NEXT_PUBLIC_API_BASE_URL: config.apiUrl,
      NEXT_PUBLIC_ENABLE_DEV_TOOLS: "true"
    }
  });
  await waitForHttp("frontend", `http://${config.frontendHost}:${config.frontendPort}`);

  log("local-dev", "ready");
  log("local-dev", `PWA:       http://${config.frontendHost}:${config.frontendPort}`);
  log("local-dev", `Dashboard: http://${config.frontendHost}:${config.frontendPort}/dashboard/login`);
  log("local-dev", "Dashboard users: operator.local@example.test, ngo-admin.local@example.test, super-admin.local@example.test");
  log("local-dev", `Dashboard access code: ${config.dashboardCode}`);
  log("local-dev", "Press Ctrl+C to stop backend/frontend/Redis started by this command.");
}

main().catch((error) => {
  log("local-dev", error instanceof Error ? error.message : String(error));
  shutdown(1);
});
