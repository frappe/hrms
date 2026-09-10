import frappeUIPreset, { content as frappeUIContent } from "frappe-ui/tailwind";

export default {
	presets: [frappeUIPreset],
	content: [
		...frappeUIContent,
		"./index.html",
		"./src/**/*.{vue,js,ts,jsx,tsx}",
		// Regional/custom apps name their sidebar icons as lucide-* strings in
		// their own portal.py. Tailwind only emits classes it can see, so those
		// files are scanned too — a glob is the whole coupling; no code is shared.
		"../../*/portal.py",
		"../../*/*/portal.py",
	],
	theme: {
		extend: {
			padding: {
				"safe-bottom": "env(safe-area-inset-bottom)",
			},
		},
	},
	plugins: [],
};
