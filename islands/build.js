import { buildIslands } from "@framework/ui/vite/island";

await buildIslands({
	app: "hrms",
	root: import.meta.dirname,
	entries: {
		"hrms.recruitment_dashboard": "src/recruitment_dashboard/index.js",
	},
	production: process.argv.includes("--production"),
	watch: process.argv.includes("--watch"),
});
