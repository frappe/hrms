import frappeUIPreset from "frappe-ui/src/tailwind/preset"
export default {
	presets: [frappeUIPreset],
	content: [
		"./index.html",
		"./src/**/*.{vue,js,ts,jsx,tsx}",
		"./node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}",
		"../node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}",
	],
	theme: {
		extend: {
			colors: {
				theme: {
					// Button colors
					"primary-button": "var(--sp-primary-button, #000000)",
					"primary-button-hover": "var(--sp-primary-button-hover, #6c757d)",
					"primary-button-text": "var(--sp-primary-button-text, #ffffff)",
					"primary-button-text-hover": "var(--sp-primary-button-text-hover, #ffffff)",

					"secondary-button": "var(--sp-secondary-button, #f4f5f6)",
					"secondary-button-hover": "var(--sp-secondary-button-hover, #ededed)",
					"secondary-button-text": "var(--sp-secondary-button-text, #000000)",
					"secondary-button-text-hover": "var(--sp-secondary-button-text-hover, #000000)",

					// Background colors
					"body-bg": "var(--sp-body-bg, #f4f5f6)",
					"content-box-bg": "var(--sp-content-box-bg, #ffffff)",
					"content-box-border": "var(--sp-content-box-border, #e5e7eb)",
					"sidebar-bg": "var(--sp-sidebar-bg, #f8f9fa)",

					// Login page colors
					"login-page-bg": "var(--sp-login-page-bg, #f4f5f6)",
					"login-box-bg": "var(--sp-login-box-bg, #ffffff)",
					"login-button-bg": "var(--sp-login-button-bg, #000000)",
					"login-button-hover": "var(--sp-login-button-hover, #6c757d)",
					"login-button-text": "var(--sp-login-button-text, #ffffff)",
					"login-button-text-hover": "var(--sp-login-button-text-hover, #ffffff)",
					"login-heading-text": "var(--sp-login-heading-text, #212529)",

					// Text colors
					"content-box-text": "var(--sp-content-box-text, #1F2937)",
					"content-box-text-secondary": "var(--sp-content-box-text-secondary, #6c757d)",
					"sidebar-text": "var(--sp-sidebar-text, #1F2937)",
					"page-heading": "var(--sp-page-heading, #111827)",
					text: "var(--sp-text, #1F2937)",

					// Input colors
					"input-bg": "var(--sp-input-bg, #ffffff)",
					"input-border": "var(--sp-input-border, #d1d5db)",
					"input-text": "var(--sp-input-text, #1f2937)",
					"input-label": "var(--sp-input-label, #374151)",

					// Other colors
					link: "var(--sp-link, #000000)",
					primary: "var(--sp-primary, #000000)",
					secondary: "var(--sp-secondary, #6c757d)",
				},
			},
			screens: {
				standalone: {
					raw: "(display-mode: standalone)",
				},
			},
			padding: {
				"safe-top": "env(safe-area-inset-top)",
				"safe-right": "env(safe-area-inset-right)",
				"safe-bottom": "env(safe-area-inset-bottom)",
				"safe-left": "env(safe-area-inset-left)",
			},
		},
	},
	plugins: [],
}
