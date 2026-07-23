import { createServer } from "node:http";
import { createReadStream, promises as fs } from "node:fs";
import { dirname, extname, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const HOST = "127.0.0.1";
const PORT = 43127;
const ROOT = dirname(fileURLToPath(import.meta.url));
const ROOT_REAL = await fs.realpath(ROOT);

const MIME = new Map([
  [".html", "text/html; charset=utf-8"],
  [".css", "text/css; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
  [".mjs", "text/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".md", "text/markdown; charset=utf-8"],
  [".png", "image/png"],
  [".svg", "image/svg+xml"],
  [".ico", "image/x-icon"]
]);

const HEADERS = {
  "Cache-Control": "no-store",
  "Content-Security-Policy": "default-src 'self' data: blob:; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
  "Cross-Origin-Opener-Policy": "same-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=(), serial=(), bluetooth=()",
  "Referrer-Policy": "no-referrer",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY"
};

const server = createServer(async (request, response) => {
  try {
    if (!request.url || !["GET", "HEAD"].includes(request.method || "")) {
      respond(response, 405, "Method Not Allowed", "text/plain; charset=utf-8", request.method === "HEAD");
      return;
    }

    const requestUrl = new URL(request.url, `http://${HOST}:${PORT}`);
    if (requestUrl.pathname === "/health") {
      respond(response, 200, JSON.stringify({ status: "ok", product: "DISCOVER-NURSE-AI-OS-MISSION-CONTROL", version: "2.0.0", integration: "manual_handoff", externalActions: false }), "application/json; charset=utf-8", request.method === "HEAD");
      return;
    }

    let pathname;
    try { pathname = decodeURIComponent(requestUrl.pathname); }
    catch { respond(response, 400, "Bad Request", "text/plain; charset=utf-8", request.method === "HEAD"); return; }
    if (pathname.includes("\0") || pathname.includes("\\")) {
      respond(response, 400, "Bad Request", "text/plain; charset=utf-8", request.method === "HEAD");
      return;
    }
    if (pathname === "/") pathname = "/index.html";

    const candidate = resolve(ROOT, `.${pathname}`);
    if (!(candidate === ROOT_REAL || candidate.startsWith(`${ROOT_REAL}${sep}`))) {
      respond(response, 403, "Forbidden", "text/plain; charset=utf-8", request.method === "HEAD");
      return;
    }
    const real = await fs.realpath(candidate).catch(() => null);
    if (!real || !(real === ROOT_REAL || real.startsWith(`${ROOT_REAL}${sep}`))) {
      respond(response, 404, "Not Found", "text/plain; charset=utf-8", request.method === "HEAD");
      return;
    }
    const stat = await fs.stat(real);
    if (!stat.isFile()) {
      respond(response, 404, "Not Found", "text/plain; charset=utf-8", request.method === "HEAD");
      return;
    }

    response.writeHead(200, {
      ...HEADERS,
      "Content-Length": stat.size,
      "Content-Type": MIME.get(extname(real).toLowerCase()) || "application/octet-stream"
    });
    if (request.method === "HEAD") response.end();
    else createReadStream(real).pipe(response);
  } catch (_error) {
    if (!response.headersSent) respond(response, 500, "Local Server Error", "text/plain; charset=utf-8", request.method === "HEAD");
    else response.destroy();
  }
});

server.on("error", (error) => {
  if (error && error.code === "EADDRINUSE") {
    console.error(`DISCOVER stopped: ${HOST}:${PORT} is already in use. Close the other process or use portable index.html mode.`);
  } else {
    console.error("DISCOVER local server could not start.", error && error.message ? error.message : error);
  }
  process.exitCode = 1;
});

server.listen(PORT, HOST, () => {
  console.log(`DISCOVER · Nurse AI OS Mission Control v2.0.0 is available at http://${HOST}:${PORT}/`);
  console.log("This static server is bound to this computer only. No agent or external action is running. Press Control+C to stop.");
});

function respond(response, status, body, type, headOnly) {
  const bytes = Buffer.from(body);
  response.writeHead(status, { ...HEADERS, "Content-Length": bytes.length, "Content-Type": type });
  response.end(headOnly ? undefined : bytes);
}
