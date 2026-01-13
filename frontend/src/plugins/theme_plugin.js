/**
 * HRMS Service Portal Theme Plugin for Vue 3
 * Integrates with hrms_service_portal_theme app
 */

export default function createThemePlugin() {
	return {
		install(app) {
			// Initialize theme on plugin install
			initTheme()

			// Set up real-time updates listener
			setupRealtimeUpdates()

			console.log("[HRMS Theme Plugin] Installed successfully")
		},
	}
}

/**
 * Fetch and apply theme from backend
 */
async function initTheme() {
	try {
		const response = await fetch("/api/method/hrms.api.theme_api.get_theme", {
			credentials: "same-origin",
			headers: {
				Accept: "application/json",
				"Content-Type": "application/json",
			},
		})

		if (!response.ok) {
			console.warn("[HRMS Theme] API not available")
			return
		}

		const result = await response.json()
		const theme = result.message || result

		if (!theme || Object.keys(theme).length === 0) {
			console.warn("[HRMS Theme] No theme data returned from API")
			return
		}

		// Check if theme has actual color data (not just empty fields)
		const hasThemeData =
			theme.primary_button_color || theme.body_content_box_bg || theme.link_color

		if (!hasThemeData) {
			console.log("[HRMS Theme] Theme data exists but no colors configured")
			return
		}

		console.log("[HRMS Theme] Theme data received:", {
			primary_button: theme.primary_button_color,
			secondary_button: theme.secondary_button_color,
			body_bg: theme.body_bg || theme.body__bg,
			content_box_bg: theme.body_content_box_bg,
			sidebar_bg: theme.sidebar_bg,
			link: theme.link_color,
			modified: theme.modified,
			page_heading_text_color: theme.page_heading_text_color,
			login_heading: theme.login_heading_text_color,
			login_page_title: theme.login_page_title,
			secondary_text: theme.body_content_box_text_secondary_color,
			input_bg: theme.input_bg,
			input_border: theme.input_border,
			input_text: theme.input_text,
			input_label: theme.input_label,
			content_box_text_secondary: theme.body_content_box_text_secondary_color,
		})

		// Apply CSS variables
		applyTheme(theme)

		console.log("[HRMS Theme] Applied successfully")
	} catch (error) {
		console.error("[HRMS Theme] Failed to load:", error)
	}
}

/**
 * Apply theme CSS variables to document root
 */
function applyTheme(theme) {
	const root = document.documentElement

	// Helper: set CSS var only when value is non-empty
	const setIf = (name, value) => {
		if (value !== undefined && value !== null && value !== "") {
			root.style.setProperty(name, value)
		}
	}

	// Primary Button
	setIf("--sp-primary-button", theme.primary_button_color)
	setIf("--sp-primary-button-hover", theme.primary_button_hover)
	setIf("--sp-primary-button-text", theme.primary_button_text)
	setIf("--sp-primary-button-text-hover", theme.primary_button_text_hover)

	// Secondary Button
	setIf("--sp-secondary-button", theme.secondary_button_color)
	setIf("--sp-secondary-button-hover", theme.secondary_button_hover)
	setIf("--sp-secondary-button-text", theme.secondary_button_text)
	setIf("--sp-secondary-button-text-hover", theme.secondary_button_text_hover)

	// Body & Content
	setIf("--sp-body-bg", theme.body_bg || theme.body__bg)
	setIf("--sp-content-box-bg", theme.body_content_box_bg)
	setIf("--sp-content-box-text", theme.body_content_box_text_color)
	setIf("--sp-content-box-text-secondary", theme.body_content_box_text_secondary_color)

	// Sidebar
	setIf("--sp-sidebar-bg", theme.sidebar_bg)
	setIf("--sp-sidebar-text", theme.sidebar_text)

	// Login Page (allow fallback to primary button when login-specific value missing)
	setIf("--sp-login-button-bg", theme.login_button_bg || theme.primary_button_color)
	setIf("--sp-login-button-hover", theme.login_button_hover_bg || theme.primary_button_hover)
	setIf("--sp-login-button-text", theme.login_button_text)
	setIf("--sp-login-button-text-hover", theme.login_button_text_hover)
	setIf("--sp-login-page-bg", theme.login_page_bg)
	setIf("--sp-login-box-bg", theme.login_box_bg)
	setIf("--sp-login-heading-text", theme.login_heading_text_color)

	// Links & Headings
	setIf("--sp-link", theme.link_color)
	setIf("--sp-page-heading", theme.page_heading_text_color)

	// Input Fields
	setIf("--sp-input-bg", theme.input_bg)
	setIf("--sp-input-border", theme.input_border)
	setIf("--sp-input-text", theme.input_text)
	setIf("--sp-input-label", theme.input_label)

	// Backward compatibility aliases
	setIf("--sp-primary", theme.primary_button_color)
	setIf("--sp-secondary", theme.secondary_button_color)
	setIf("--sp-text", theme.body_content_box_text_color)

	// Apply custom CSS if provided
	if (theme.custom_css) {
		let styleElement = document.getElementById("sp-custom-css")
		if (!styleElement) {
			styleElement = document.createElement("style")
			styleElement.id = "sp-custom-css"
			document.head.appendChild(styleElement)
		}
		styleElement.textContent = theme.custom_css
	}

	console.log("[HRMS Theme] CSS Variables applied:", {
		primaryButton: theme.primary_button_color,
		secondaryButton: theme.secondary_button_color,
		bodyBg: theme.body_bg,
		contentBoxBg: theme.body_content_box_bg,
		contentText: theme.body_content_box_text_color,
		sidebarBg: theme.sidebar_bg,
		link: theme.link_color,
		pageHeading: theme.page_heading_text_color,
		loginHeading: theme.login_heading_text_color,
		inputBg: theme.input_bg,
		inputBorder: theme.input_border,
		inputText: theme.input_text,
		inputLabel: theme.input_label,
		secondaryText: theme.body_content_box_text_secondary_color,
	})
}

/**
 * Set up real-time updates for theme changes
 */

function setupRealtimeUpdates() {
	let retryCount = 0
	const MAX_RETRIES = 20 // ~10 seconds
	const checkRealtime = () => {
		if (window.frappe && window.frappe.realtime) {
			window.frappe.realtime.on("employee_self_service_portal_theme:update", async (data) => {
				console.log("[HRMS Theme] Real-time update received", data)
				await initTheme()
			})
			console.log("[HRMS Theme] Real-time updates enabled")
		} else if (retryCount < MAX_RETRIES) {
			retryCount++
			setTimeout(checkRealtime, 500)
		} else {
			console.warn("[HRMS Theme] Real-time updates not available after max retries")
		}
	}

	checkRealtime()
}

/**
 * Expose theme reload function globally for debugging
 */
if (typeof window !== "undefined") {
	window.reloadServicePortalTheme = initTheme
}
