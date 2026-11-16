import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiPort = Number(process.env.D4J_API_PORT ?? 8787);
const webPort = Number(process.env.D4J_WEB_PORT ?? 5173);

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: webPort,
    proxy: {
      "/api": `http://127.0.0.1:${apiPort}`,
    },
  },
});
