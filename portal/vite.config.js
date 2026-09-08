import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { VitePWA } from "vite-plugin-pwa";
import frappeui from "frappe-ui/vite";

import path from "path";

export default defineConfig({
	server: {
		port: 8081,
		allowedHosts: true,
	},
	plugins: [
		// handles the dev proxy, production base url, and copying index.html to www/
		frappeui({
			frontendRoute: "/hrms",
			// index.html already declares its own boot block, so skip the injected one
			jinjaBootData: false,
			buildConfig: {
				outDir: "../hrms/public/portal",
				indexHtmlPath: "../hrms/www/hrms.html",
				baseUrl: "/assets/hrms/portal/",
				emptyOutDir: true,
				sourcemap: false,
			},
		}),
		vue(),
		VitePWA({
			registerType: "autoUpdate",
			injectRegister: "auto",
			workbox: {
				globPatterns: ["**/*.{js,css,html,svg,png,woff2}"],
				navigateFallback: null,
			},
			devOptions: { enabled: false },
			manifest: {
				display: "standalone",
				name: "Frappe HR Portal",
				short_name: "HR Portal",
				start_url: "/hrms",
				scope: "/hrms",
				id: "/hrms",
				description: "Your HR portal: attendance, leave, pay and profile",
				theme_color: "#ffffff",
				background_color: "#ffffff",
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
		target: "es2015",
		rollupOptions: {
			output: {
				manualChunks: {
					"frappe-ui": ["frappe-ui"],
				},
			},
		},
	},
	optimizeDeps: {
		include: ["feather-icons", "showdown", "tailwind.config.js", "engine.io-client"],
	},
});
