function makeTranslationFunction() {
	let messages = {};
	return {
		translate,
		load: () => Promise.allSettled([
			setup(),
			// TODO: load dayjs locales
		]),
	}

	async function setup() {
		if (window.frappe?.boot?.__messages) {
			messages = window.frappe?.boot?.__messages;
			return;
		}

		const url = new URL("/api/method/frappe.translate.load_all_translations", location.origin);
		const lang = normalizeLang(window.frappe?.boot?.lang ?? navigator.language);
		url.searchParams.append("lang", lang);
		url.searchParams.append("hash", window.frappe?.boot?.translations_hash || window._version_number || Math.random()); // for cache busting
		// url.searchParams.append("app", "hrms");

		try {
			const response = await fetch(url);
			messages = await response.json() || {}
		} catch (error) {
			console.error("Failed to fetch translations:", error)
		}
	}

	function translate(txt, replace, context = null) {
		if (!txt || typeof txt != "string") return txt;

		let translated_text = "";
		let key = txt;
		if (context) {
			translated_text = messages[`${key}:${context}`];
		}
		if (!translated_text) {
			translated_text = messages[key] || txt;
		}
		if (replace && typeof replace === "object") {
			translated_text = format(translated_text, replace);
		}

		return translated_text;
	}

	function format(str, args) {
		if (str == undefined) return str;

		let unkeyed_index = 0;
		return str.replace(
			/\{(\w*)\}/g,
			(match, key) => {
				if (key === "") {
					key = unkeyed_index;
					unkeyed_index++;
				}
				if (key == +key) {
					return args[key] !== undefined ? args[key] : match;
				}
			}
		);
	}
}

const { translate, load } = makeTranslationFunction();

export const translationsPlugin = {
	async isReady() {
		await load();
	},
	install(/** @type {import('vue').App} */ app, options) {
		const __ = translate;
		// app.mixin({ methods: { __ } })
		app.config.globalProperties.__ = __;
		app.provide("$translate", __);
	},
}

function normalizeLang(input) {
	if (!input) return "en";
	let s = String(input);
	// unify separators first
	s = s.replace("-", "_");
	const lower = s.toLowerCase();
	// Region-specific codes that Frappe expects with underscore
	const special = {
		"pt_br": "pt_BR",
		"zh_tw": "zh_TW",
		"sr_cs": "sr_CS",
		"zh_cn": "zh_CN",
	};
	if (special[lower]) return special[lower];
	// default to two-letter base (e.g., vi, de, fr)
	return lower.slice(0, 2);
}

// Exported for testing/diagnostics
export { normalizeLang };
