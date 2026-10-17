import assert from "node:assert/strict"
import { after, before, test } from "node:test"
import { fileURLToPath } from "node:url"
import { createServer } from "vite"

let server, dayjs, loadDayjsLocale, translationsPlugin
const originalNavigator = Object.getOwnPropertyDescriptor(globalThis, "navigator")
const originalWindow = Object.getOwnPropertyDescriptor(globalThis, "window")

before(async () => {
	const root = fileURLToPath(new URL("../", import.meta.url))
	server = await createServer({
		configFile: false,
		root,
		resolve: { alias: { "@": `${root}src` } },
		server: { middlewareMode: true },
		appType: "custom",
	})
	;({ default: dayjs, loadDayjsLocale } = await server.ssrLoadModule("/src/utils/dayjs.js"))
	;({ translationsPlugin } = await server.ssrLoadModule("/src/plugins/translationsPlugin.js"))
	Object.defineProperty(globalThis, "navigator", {
		configurable: true,
		value: { language: "fr-FR" },
	})
	globalThis.window = {}
})

after(async () => {
	await server?.close()
	for (const [key, descriptor] of [
		["navigator", originalNavigator],
		["window", originalWindow],
	]) {
		if (descriptor) Object.defineProperty(globalThis, key, descriptor)
		else delete globalThis[key]
	}
})

test("formats holiday dates, calendar months, and localized formats in German", async () => {
	await loadDayjsLocale("de")
	const date = dayjs("2026-03-16")
	assert.equal(date.format("ddd, D MMM YYYY"), "Mo., 16 März 2026")
	assert.equal(date.format("MMMM"), "März")
	assert.equal(date.format("LL"), "16. März 2026")
	assert.equal(date.format("YYYY-MM-DD"), "2026-03-16")
})

test("normalizes Frappe regional locale codes", async () => {
	await loadDayjsLocale("pt_BR")
	assert.equal(dayjs.locale(), "pt-br")
	assert.equal(dayjs("2026-03-16").format("LL"), "16 de março de 2026")
	await loadDayjsLocale("de_AT")
	assert.equal(dayjs.locale(), "de-at")
})

test("falls back to the parent language for unsupported regions", async () => {
	await loadDayjsLocale("fr-XX")
	assert.equal(dayjs.locale(), "fr")
	assert.equal(dayjs("2026-03-16").format("ddd, D MMM YYYY"), "lun., 16 mars 2026")
})

test("falls back to English for unsupported or missing languages", async () => {
	for (const language of ["unknown-XX", undefined, "en"]) {
		await loadDayjsLocale("de")
		await loadDayjsLocale(language)
		assert.equal(dayjs.locale(), "en")
		assert.equal(dayjs("2026-03-16").format("ddd, D MMM YYYY"), "Mon, 16 Mar 2026")
	}
})

test("translation readiness uses the Frappe language even with boot messages", async () => {
	window.frappe = { boot: { lang: "de", __messages: {} } }
	await translationsPlugin.isReady()
	assert.equal(dayjs.locale(), "de")
})

test("translation readiness uses the browser language when boot has none", async () => {
	window.frappe = { boot: { __messages: {} } }
	await translationsPlugin.isReady()
	assert.equal(dayjs.locale(), "fr")
})
