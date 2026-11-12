import { buildIslands } from "@framework/ui/vite/island";

await buildIslands({
  app: "hrms",
  root: import.meta.dirname,
  entries: {
    "hrms.checklist": "src/checklist.js",
  },
  production: process.argv.includes("--production"),
  watch: process.argv.includes("--watch"),
});
