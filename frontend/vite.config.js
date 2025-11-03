import { createRequire } from "node:module";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const require = createRequire(import.meta.url);
const mockedWorkspaces = require("./src/mocks/workspaces.json");

function respondJson(res, statusCode, payload) {
  if (res.writableEnded) {
    return;
  }

  res.statusCode = statusCode;
  res.setHeader("Content-Type", "application/json");
  res.setHeader("Cache-Control", "no-store");
  res.end(JSON.stringify(payload));
}

function isWorkspaceListingRequest(req) {
  if (req.method !== "GET") {
    return false;
  }

  const url = req.url ?? "";
  return (
    url === "/api/workspaces" ||
    url === "/workspaces" ||
    url.startsWith("/api/workspaces?") ||
    url.startsWith("/workspaces?")
  );
}

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        configure(proxy) {
          proxy.on("error", (error, req, res) => {
            if (res.writableEnded) {
              return;
            }

            if (error.code === "ECONNREFUSED" && isWorkspaceListingRequest(req)) {
              console.warn(
                "[dev-server] backend unavailable. Serving mocked /api/workspaces response."
              );
              respondJson(res, 200, mockedWorkspaces);
              return;
            }

            console.error(
              `[dev-server] proxy error for ${req.method ?? ""} ${req.url ?? ""}: ${error.message}`
            );
            respondJson(res, 502, {
              code: error.code ?? "PROXY_ERROR",
              message: "Backend API is unreachable."
            });
          });
        }
      }
    }
  }
});
