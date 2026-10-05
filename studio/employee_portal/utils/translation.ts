// same as the PWA's frontend/src/plugins/translationsPlugin.js
import { ref } from "vue";

const messages = ref<Record<string, string>>({});
let request: Promise<void> | null = null;

export function loadTranslations() {
	request ??= fetchTranslations();
	return request;
}

export function __(text: string, replace?: unknown[] | Record<string, unknown>, context?: string) {
	if (!text || typeof text !== "string") return text;
	const translated =
		(context && messages.value[`${text}:${context}`]) || messages.value[text] || text;
	return replace ? format(translated, replace) : translated;
}

async function fetchTranslations() {
	const url = new URL("/api/method/frappe.translate.get_boot_translations", location.origin);
	url.searchParams.append("lang", navigator.language);
	try {
		const response = await fetch(url);
		const data = await response.json();
		messages.value = data?.message ?? {};
	} catch (error) {
		console.error("Failed to fetch translations:", error);
	}
}

function format(text: string, args: unknown[] | Record<string, unknown>) {
	let index = 0;
	return text.replace(/\{(\w*)\}/g, (match, key) => {
		const value =
			key === "" ? (args as unknown[])[index++] : (args as Record<string, unknown>)[key];
		return value !== undefined ? String(value) : match;
	});
}
