import { createServer } from "node:http";
import { existsSync, readFileSync } from "node:fs";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const workspaceRoot = path.resolve(__dirname, "..", "..");
const dashboardRoot = __dirname;
const port = Number(process.env.PORT ?? 4187);
const authorityMarkerName = ".workspace_authority.json";

const staticFiles = {
  "/": { filePath: path.join(dashboardRoot, "index.html"), contentType: "text/html; charset=utf-8" },
  "/app.js": { filePath: path.join(dashboardRoot, "app.js"), contentType: "text/javascript; charset=utf-8" },
  "/control-room": {
    filePath: path.join(dashboardRoot, "control-room.html"),
    contentType: "text/html; charset=utf-8",
  },
  "/control-room.js": {
    filePath: path.join(dashboardRoot, "control-room.js"),
    contentType: "text/javascript; charset=utf-8",
  },
  "/styles.css": { filePath: path.join(dashboardRoot, "styles.css"), contentType: "text/css; charset=utf-8" },
};

function validateWorkspaceAuthority(rootPath) {
  const markerPath = path.join(rootPath, authorityMarkerName);
  if (!existsSync(markerPath)) {
    throw new Error(`operator wall root is missing ${authorityMarkerName}; authoritative workspace marker required.`);
  }
  let marker;
  try {
    marker = JSON.parse(readFileSync(markerPath, "utf8"));
  } catch (error) {
    throw new Error(`operator wall root has an invalid ${authorityMarkerName}.`);
  }
  if (!marker || typeof marker !== "object") {
    throw new Error(`operator wall root has an invalid ${authorityMarkerName}.`);
  }
  if (marker.authority_status !== "authoritative") {
    throw new Error(`operator wall root has an invalid ${authorityMarkerName}; authority_status must equal "authoritative".`);
  }
  if (typeof marker.canonical_root_hint !== "string" || !marker.canonical_root_hint.trim()) {
    throw new Error(`operator wall root has an invalid ${authorityMarkerName}; canonical_root_hint is required.`);
  }
  if (path.resolve(marker.canonical_root_hint) !== rootPath) {
    throw new Error(
      `operator wall root has an invalid ${authorityMarkerName}; canonical_root_hint must resolve to the authoritative workspace root.`,
    );
  }
}

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
  });
  response.end(JSON.stringify(payload));
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
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(workspaceRoot, "scripts", "operator_wall_snapshot.py");
    const child = spawn(resolvePython(), [scriptPath, "--project", projectName], {
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
        reject(new Error(stderr.trim() || stdout.trim() || `Snapshot reader exited with code ${code}.`));
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(error);
      }
    });
  });
}

function readRunDetails(runId) {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(workspaceRoot, "scripts", "operator_api.py");
    const child = spawn(resolvePython(), [scriptPath, "run-details", "--run-id", runId], {
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
        reject(new Error(stderr.trim() || stdout.trim() || `Run-details reader exited with code ${code}.`));
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(error);
      }
    });
  });
}

function readTaskDetails(taskId) {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(workspaceRoot, "scripts", "operator_api.py");
    const child = spawn(resolvePython(), [scriptPath, "task-details", "--task-id", taskId], {
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
        reject(new Error(stderr.trim() || stdout.trim() || `Task-details reader exited with code ${code}.`));
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(error);
      }
    });
  });
}

const server = createServer(async (request, response) => {
  try {
    const url = new URL(request.url ?? "/", `http://${request.headers.host ?? "localhost"}`);
    if (url.pathname === "/api/snapshot") {
      const projectName = url.searchParams.get("project") || "all";
      const snapshot = await readSnapshot(projectName);
      sendJson(response, 200, snapshot);
      return;
    }

    if (url.pathname === "/api/run-details") {
      if ((request.method ?? "GET").toUpperCase() !== "GET") {
        response.writeHead(405, {
          "Content-Type": "application/json; charset=utf-8",
          Allow: "GET",
          "Cache-Control": "no-store",
        });
        response.end(JSON.stringify({ error: "Method not allowed." }));
        return;
      }
      const runId = (url.searchParams.get("run_id") || "").trim();
      if (!runId) {
        sendJson(response, 400, { error: "run_id is required." });
        return;
      }
      const details = await readRunDetails(runId);
      sendJson(response, 200, details);
      return;
    }

    if (url.pathname === "/api/task-details") {
      if ((request.method ?? "GET").toUpperCase() !== "GET") {
        response.writeHead(405, {
          "Content-Type": "application/json; charset=utf-8",
          Allow: "GET",
          "Cache-Control": "no-store",
        });
        response.end(JSON.stringify({ error: "Method not allowed." }));
        return;
      }
      const taskId = (url.searchParams.get("task_id") || "").trim();
      if (!taskId) {
        sendJson(response, 400, { error: "task_id is required." });
        return;
      }
      const details = await readTaskDetails(taskId);
      sendJson(response, 200, details);
      return;
    }

    const staticFile = staticFiles[url.pathname];
    if (staticFile) {
      const contents = await readFile(staticFile.filePath);
      response.writeHead(200, {
        "Content-Type": staticFile.contentType,
        "Cache-Control": "no-store",
      });
      response.end(contents);
      return;
    }

    sendJson(response, 404, { error: "Not found" });
  } catch (error) {
    sendJson(response, 500, { error: error instanceof Error ? error.message : String(error) });
  }
});

validateWorkspaceAuthority(workspaceRoot);

server.listen(port, () => {
  console.log(`Studio operator wall running at http://localhost:${port}`);
});
