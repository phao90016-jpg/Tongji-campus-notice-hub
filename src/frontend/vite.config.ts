import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    proxy: {
      // 开发期把 /api 转发到本地后端，避免跨域
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
