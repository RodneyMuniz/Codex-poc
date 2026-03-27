import { createServer } from "node:http";
import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const workspaceRoot = path.resolve(__dirname, "..", "..");
const dashboardRoot = __dirname;
const port = Number(process.env.PORT ?? 4187);

const staticFiles = {
  "/": { filePath: path.join(dashboardRoot, "index.html"), contentType: "text/html; charset=utf-8" },
  "/app.js": { filePath: path.join(dashboardRoot, "app.js"), contentType: "text/javascript; charset=utf-8" },
  "/styles.css": { filePath: path.join(dashboardRoot, "styles.css"), contentType: "text/css; charset=utf-8" },
};

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

const server = createServer(async (request, response) => {
  try {
    const url = new URL(request.url ?? "/", `http://${request.headers.host ?? "localhost"}`);
    if (url.pathname === "/api/snapshot") {
      const projectName = url.searchParams.get("project") || "all";
      const snapshot = await readSnapshot(projectName);
      sendJson(response, 200, snapshot);
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

server.listen(port, () => {
  console.log(`Studio operator wall running at http://localhost:${port}`);
});
