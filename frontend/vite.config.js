import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const backendTarget = process.env.VITE_PROXY_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/intake": {
        target: backendTarget,
        changeOrigin: true
      },
      "/work": {
        target: backendTarget,
        changeOrigin: true
      },
      "/autonomous": {
        target: backendTarget,
        changeOrigin: true
      },
      "/api": {
        target: backendTarget,
        changeOrigin: true
      }
    }
  }
});
