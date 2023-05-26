import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import { VitePWA } from "vite-plugin-pwa"

import path from "path"
import { getProxyOptions } from "frappe-ui/src/utils/vite-dev-server"
import { webserver_port } from "../../../sites/common_site_config.json"

// https://vitejs.dev/config/
export default defineConfig({
	plugins: [
		vue(),
		VitePWA({
			registerType: "autoUpdate",
			devOptions: {
				enabled: true,
			},
			manifest: {
				display: "standalone",
				name: "Frappe HR",
				short_name: "Frappe HR",
				description: "Everyday HR & Payroll operations at your fingertips",
				icons: [
					{
						"src": "/assets/hrms/manifest/manifest-icon-192.maskable.png",
						"sizes": "192x192",
						"type": "image/png",
						"purpose": "any"
					},
					{
						"src": "/assets/hrms/manifest/manifest-icon-192.maskable.png",
						"sizes": "192x192",
						"type": "image/png",
						"purpose": "maskable"
					},
					{
						"src": "/assets/hrms/manifest/manifest-icon-512.maskable.png",
						"sizes": "512x512",
						"type": "image/png",
						"purpose": "any"
					},
					{
						"src": "/assets/hrms/manifest/manifest-icon-512.maskable.png",
						"sizes": "512x512",
						"type": "image/png",
						"purpose": "maskable"
					}
				]
			}
		}),
	],
	server: {
		port: 8080,
		proxy: getProxyOptions({ port: webserver_port }),
	},
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "src"),
		},
	},
	build: {
		outDir: `../${path.basename(path.resolve(".."))}/public/frontend`,
		emptyOutDir: true,
		target: "es2015",
	},
	optimizeDeps: {
		include: ["frappe-ui > feather-icons", "showdown", "engine.io-client"],
	},
})
