import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/intake": {
        target: "http://localhost:8000",
        changeOrigin: true
      },
      "/work": {
        target: "http://localhost:8000",
        changeOrigin: true
      },
      "/autonomous": {
        target: "http://localhost:8000",
        changeOrigin: true
      },
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true
      }
    }
  }
});
