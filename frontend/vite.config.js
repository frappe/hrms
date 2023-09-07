import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import { VitePWA } from "vite-plugin-pwa"

import path from "path"
import frappeui from "frappe-ui/vite"

export default defineConfig({
	plugins: [
		frappeui(),
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
				start_url: "/hrms",
				description: "Everyday HR & Payroll operations at your fingertips",
				icons: [
					{
						src: "/assets/hrms/manifest/manifest-icon-192.maskable.png",
						sizes: "192x192",
						type: "image/png",
						purpose: "any",
					},
					{
						src: "/assets/hrms/manifest/manifest-icon-192.maskable.png",
						sizes: "192x192",
						type: "image/png",
						purpose: "maskable",
					},
					{
						src: "/assets/hrms/manifest/manifest-icon-512.maskable.png",
						sizes: "512x512",
						type: "image/png",
						purpose: "any",
					},
					{
						src: "/assets/hrms/manifest/manifest-icon-512.maskable.png",
						sizes: "512x512",
						type: "image/png",
						purpose: "maskable",
					},
				],
			},
		}),
	],
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "src"),
		},
	},
	build: {
		outDir: "../hrms/public/frontend",
		emptyOutDir: true,
		target: "es2015",
		commonjsOptions: {
			include: [/tailwind.config.js/, /node_modules/],
		},
	},
	optimizeDeps: {
		include: [
			"feather-icons",
			"showdown",
			"tailwind.config.js",
			"engine.io-client",
		],
	},
})
