import { defineConfig } from "@playwright/test";
import path from "node:path";
const python =
  process.platform === "win32"
    ? "../.venv/Scripts/python.exe"
    : "../.venv/bin/python";
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  timeout: 30000,
  use: {
    baseURL: "http://127.0.0.1:5173",
    viewport: { width: 1440, height: 1100 },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: `"${path.resolve(python)}" -m uvicorn app.main:app --app-dir ../backend --host 127.0.0.1 --port 8000`,
      url: "http://127.0.0.1:8000/api/health",
      reuseExistingServer: !process.env.CI,
      env: { EXPLANATION_PROVIDER: "template" },
    },
    {
      command: "node node_modules/vite/bin/vite.js --host 127.0.0.1",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !process.env.CI,
    },
  ],
});
