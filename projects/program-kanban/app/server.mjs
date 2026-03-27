import { createServer } from "node:http";
import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const workspaceRoot = path.resolve(__dirname, "..", "..", "..");
const dashboardRoot = __dirname;
const port = Number(process.env.PORT ?? 4187);
const launcherPaths = {
  statusFile: path.join(dashboardRoot, "offline-launcher.status.json"),
  helperFile: path.join(dashboardRoot, "open-studio-launcher.cmd"),
  commandFile: path.join(dashboardRoot, "launch-studio.cmd"),
  scriptFile: path.join(dashboardRoot, "launch-studio.ps1"),
  appLogs: {
    "program-kanban": {
      name: "Program Kanban",
      url: "http://localhost:4187",
      stdout: path.join(workspaceRoot, "sessions", "runtime_logs", "program-kanban.out.log"),
      stderr: path.join(workspaceRoot, "sessions", "runtime_logs", "program-kanban.err.log"),
    },
    "tactics-game": {
      name: "TacticsGame",
      url: "http://127.0.0.1:4173",
      stdout: path.join(workspaceRoot, "sessions", "runtime_logs", "tactics-game.out.log"),
      stderr: path.join(workspaceRoot, "sessions", "runtime_logs", "tactics-game.err.log"),
    },
  },
};

const staticFiles = {
  "/": { filePath: path.join(dashboardRoot, "index.html"), contentType: "text/html; charset=utf-8" },
  "/app.js": { filePath: path.join(dashboardRoot, "app.js"), contentType: "text/javascript; charset=utf-8" },
  "/styles.css": { filePath: path.join(dashboardRoot, "styles.css"), contentType: "text/css; charset=utf-8" },
  "/offline-launcher.html": { filePath: path.join(dashboardRoot, "offline-launcher.html"), contentType: "text/html; charset=utf-8" },
  "/open-studio-launcher.cmd": { filePath: launcherPaths.helperFile, contentType: "text/plain; charset=utf-8" },
  "/launch-studio.cmd": { filePath: launcherPaths.commandFile, contentType: "text/plain; charset=utf-8" },
};

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  });
  response.end(JSON.stringify(payload));
}

function sendText(response, statusCode, body) {
  response.writeHead(statusCode, {
    "Content-Type": "text/plain; charset=utf-8",
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  });
  response.end(body);
}

function resolvePython() {
  const candidates = [
    path.join(workspaceRoot, "venv", "Scripts", "python.exe"),
    path.join(workspaceRoot, "venv", "bin", "python"),
    process.env.PYTHON,
    "python",
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (!candidate.includes(path.sep) || existsSync(candidate)) {
      return candidate;
    }
  }

  return "python";
}

function readSnapshot(projectName) {
  const scriptPath = path.join(workspaceRoot, "scripts", "operator_wall_snapshot.py");
  return runPythonJson([scriptPath, "--project", projectName], "Snapshot reader");
}

function runPythonJson(args, label = "Python helper") {
  return new Promise((resolve, reject) => {
    const child = spawn(resolvePython(), args, {
      cwd: workspaceRoot,
      env: process.env,
      windowsHide: true,
    });

    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", (error) => reject(error));
    child.on("close", (code) => {
      if (code !== 0) {
        const rawError = stdout.trim() || stderr.trim() || `${label} exited with code ${code}.`;
        try {
          const parsed = JSON.parse(rawError);
          reject(new Error(parsed.error || parsed.message || `${label} failed.`));
          return;
        } catch {
          reject(new Error(rawError));
          return;
        }
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(error);
        return;
      }
    });
  });
}

function readJsonBody(request) {
  return new Promise((resolve, reject) => {
    let body = "";
    request.on("data", (chunk) => {
      body += chunk.toString();
      if (body.length > 1_000_000) {
        reject(new Error("Request body too large."));
      }
    });
    request.on("end", () => {
      if (!body) {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(body));
      } catch (error) {
        reject(error);
      }
    });
    request.on("error", (error) => reject(error));
  });
}

async function checkUrlStatus(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 1500);
  try {
    const response = await fetch(url, {
      method: "GET",
      cache: "no-store",
      signal: controller.signal,
    });
    return response.status;
  } catch {
    return null;
  } finally {
    clearTimeout(timeout);
  }
}

async function readLauncherStatusFile() {
  try {
    const contents = await readFile(launcherPaths.statusFile, "utf-8");
    return JSON.parse(contents);
  } catch {
    return null;
  }
}

async function buildLauncherStatus() {
  const persisted = await readLauncherStatusFile();
  const persistedApps = new Map(
    (persisted?.apps ?? []).map((app) => [String(app.name ?? "").toLowerCase(), app]),
  );

  const apps = [];
  for (const [key, config] of Object.entries(launcherPaths.appLogs)) {
    const saved = persistedApps.get(config.name.toLowerCase()) ?? {};
    const statusCode = await checkUrlStatus(config.url);
    apps.push({
      key,
      name: config.name,
      url: config.url,
      state: statusCode ? "online" : saved.state ?? "offline",
      status_code: statusCode ?? saved.status_code ?? null,
      pid: saved.pid ?? null,
      stdout_log: saved.stdout_log ?? config.stdout,
      stderr_log: saved.stderr_log ?? config.stderr,
      stdout_view_url: `/api/launcher/log?app=${encodeURIComponent(key)}&stream=stdout`,
      stderr_view_url: `/api/launcher/log?app=${encodeURIComponent(key)}&stream=stderr`,
    });
  }

  return {
    generated_at: new Date().toISOString(),
    launcher_mode: "server",
    launcher_root: dashboardRoot,
    workspace_root: workspaceRoot,
    helper_download_url: "/open-studio-launcher.cmd",
    command_download_url: "/launch-studio.cmd",
    status_file_url: "/api/launcher/status",
    apps,
  };
}

function runLauncherScript() {
  return new Promise((resolve, reject) => {
    const child = spawn(
      "powershell.exe",
      [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        launcherPaths.scriptFile,
      ],
      {
        cwd: dashboardRoot,
        env: process.env,
        windowsHide: true,
      },
    );

    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", (error) => reject(error));
    child.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(stderr.trim() || stdout.trim() || `Launcher exited with code ${code}.`));
        return;
      }
      resolve(stdout);
    });
  });
}

function resolveLauncherLogPath(appKey, stream) {
  const config = launcherPaths.appLogs[appKey];
  if (!config) {
    return null;
  }
  if (stream === "stdout") {
    return config.stdout;
  }
  if (stream === "stderr") {
    return config.stderr;
  }
  return null;
}

const server = createServer(async (request, response) => {
  try {
    const url = new URL(request.url ?? "/", `http://${request.headers.host ?? "localhost"}`);
    if (request.method === "OPTIONS") {
      response.writeHead(204, {
        "Cache-Control": "no-store",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
      });
      response.end();
      return;
    }

    if (url.pathname === "/api/snapshot") {
      const projectName = url.searchParams.get("project") || "all";
      const snapshot = await readSnapshot(projectName);
      sendJson(response, 200, snapshot);
      return;
    }

    if (url.pathname === "/api/operator/preview" && request.method === "POST") {
      const body = await readJsonBody(request);
      const payload = await runPythonJson(
        [
          path.join(workspaceRoot, "scripts", "operator_api.py"),
          "preview",
          "--project",
          String(body.project_name ?? "program-kanban"),
          "--text",
          String(body.text ?? ""),
          ...(body.clarification ? ["--clarification", String(body.clarification)] : []),
        ],
        "Operator preview",
      );
      sendJson(response, 200, payload);
      return;
    }

    if (url.pathname === "/api/operator/dispatch" && request.method === "POST") {
      const body = await readJsonBody(request);
      const payload = await runPythonJson(
        [
          path.join(workspaceRoot, "scripts", "operator_api.py"),
          "dispatch",
          "--project",
          String(body.project_name ?? "program-kanban"),
          "--text",
          String(body.text ?? ""),
          ...(body.clarification ? ["--clarification", String(body.clarification)] : []),
        ],
        "Operator dispatch",
      );
      sendJson(response, 200, payload);
      return;
    }

    if (url.pathname === "/api/operator/approve" && request.method === "POST") {
      const body = await readJsonBody(request);
      const payload = await runPythonJson(
        [
          path.join(workspaceRoot, "scripts", "operator_api.py"),
          "approve",
          "--approval-id",
          String(body.approval_id ?? ""),
          ...(body.note ? ["--note", String(body.note)] : []),
        ],
        "Operator approve",
      );
      sendJson(response, 200, payload);
      return;
    }

    if (url.pathname === "/api/operator/approve-resume" && request.method === "POST") {
      const body = await readJsonBody(request);
      const payload = await runPythonJson(
        [
          path.join(workspaceRoot, "scripts", "operator_api.py"),
          "approve-resume",
          "--approval-id",
          String(body.approval_id ?? ""),
          ...(body.note ? ["--note", String(body.note)] : []),
        ],
        "Operator approve and resume",
      );
      sendJson(response, 200, payload);
      return;
    }

    if (url.pathname === "/api/operator/reject" && request.method === "POST") {
      const body = await readJsonBody(request);
      const payload = await runPythonJson(
        [
          path.join(workspaceRoot, "scripts", "operator_api.py"),
          "reject",
          "--approval-id",
          String(body.approval_id ?? ""),
          ...(body.note ? ["--note", String(body.note)] : []),
        ],
        "Operator reject",
      );
      sendJson(response, 200, payload);
      return;
    }

    if (url.pathname === "/api/operator/resume" && request.method === "POST") {
      const body = await readJsonBody(request);
      const payload = await runPythonJson(
        [
          path.join(workspaceRoot, "scripts", "operator_api.py"),
          "resume",
          "--run-id",
          String(body.run_id ?? ""),
        ],
        "Operator resume",
      );
      sendJson(response, 200, payload);
      return;
    }

    if (url.pathname === "/api/operator/run") {
      const runId = url.searchParams.get("run_id") ?? "";
      const payload = await runPythonJson(
        [
          path.join(workspaceRoot, "scripts", "operator_api.py"),
          "run-details",
          "--run-id",
          runId,
        ],
        "Operator run details",
      );
      sendJson(response, 200, payload);
      return;
    }

    if (url.pathname === "/api/operator/routing") {
      const payload = await runPythonJson(
        [
          path.join(workspaceRoot, "scripts", "operator_api.py"),
          "routing-catalog",
        ],
        "Operator routing catalog",
      );
      sendJson(response, 200, payload);
      return;
    }

    if (url.pathname === "/api/control-room/restore" && request.method === "POST") {
      const body = await readJsonBody(request);
      const payload = await runPythonJson(
        [
          path.join(workspaceRoot, "scripts", "control_room_api.py"),
          "restore-backup",
          "--backup-id",
          String(body.backup_id ?? ""),
          "--requested-by",
          String(body.requested_by ?? "Control Room"),
        ],
        "Control room restore",
      );
      sendJson(response, 200, payload);
      return;
    }

    if (url.pathname === "/api/launcher/status") {
      const payload = await buildLauncherStatus();
      sendJson(response, 200, payload);
      return;
    }

    if (url.pathname === "/api/launcher/start" && request.method === "POST") {
      await runLauncherScript();
      const payload = await buildLauncherStatus();
      sendJson(response, 200, payload);
      return;
    }

    if (url.pathname === "/api/launcher/log") {
      const appKey = url.searchParams.get("app") ?? "";
      const stream = url.searchParams.get("stream") ?? "";
      const logPath = resolveLauncherLogPath(appKey, stream);
      if (!logPath) {
        sendJson(response, 404, { error: "Unknown launcher log target." });
        return;
      }
      try {
        const contents = await readFile(logPath, "utf-8");
        sendText(response, 200, contents);
      } catch {
        sendText(response, 200, "");
      }
      return;
    }

    const staticFile = staticFiles[url.pathname];
    if (staticFile) {
      const contents = await readFile(staticFile.filePath);
      response.writeHead(200, {
        "Content-Type": staticFile.contentType,
        "Cache-Control": "no-store",
        "Access-Control-Allow-Origin": "*",
      });
      response.end(contents);
      return;
    }

    sendJson(response, 404, { error: "Not found" });
  } catch (error) {
    sendJson(response, 500, { error: error instanceof Error ? error.message : String(error) });
  }
});

server.listen(port, () => {
  console.log(`Studio operator wall running at http://localhost:${port}`);
});
