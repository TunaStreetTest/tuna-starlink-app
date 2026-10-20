import react from "@vitejs/plugin-react";
import { defineConfig, type Connect, type Plugin } from "vite";

function noStudioApi(): Plugin {
  const deny: Connect.NextHandleFunction = (req, res, next) => {
    const path = (req as { url?: string }).url ?? "";
    if (path.startsWith("/api/")) {
      res.statusCode = 404;
      res.end("not found");
      return;
    }
    next();
  };
  return {
    name: "no-studio-api",
    configureServer(server) {
      server.middlewares.use(deny);
    },
    configurePreviewServer(server) {
      server.middlewares.use(deny);
    },
  };
}

export default defineConfig({
  plugins: [react(), noStudioApi()],
  server: {
    port: 5175,
    strictPort: true,
  },
  preview: {
    port: 5175,
    strictPort: true,
  },
});
