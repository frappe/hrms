export default function devBootFallback() {
	return {
		name: "hrms-dev-boot-fallback",
		apply: "serve",
		transformIndexHtml(html) {
			return html
				.replace(
					/window\.csrf_token\s*=.*\{\{ csrf_token \}\}.*$/m,
					'window.csrf_token = ""'
				)
				.replace(
					/window\.site_name\s*=.*\{\{ site_name \}\}.*$/m,
					"window.site_name = window.location.hostname"
				)
				.replace(/frappe\.boot\s*=\s*\{\{ boot \}\}/, "frappe.boot = {}")
		},
	}
}
