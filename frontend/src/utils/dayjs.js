import dayjs from "dayjs"
import updateLocale from "dayjs/plugin/updateLocale"
import localizedFormat from "dayjs/plugin/localizedFormat"
import relativeTime from "dayjs/plugin/relativeTime"
import isToday from "dayjs/plugin/isToday"
import isYesterday from "dayjs/plugin/isYesterday"
import isBetween from "dayjs/plugin/isBetween"

dayjs.extend(updateLocale)
dayjs.extend(localizedFormat)
dayjs.extend(relativeTime)
dayjs.extend(isToday)
dayjs.extend(isYesterday)
dayjs.extend(isBetween)

const locales = import.meta.glob("../../node_modules/dayjs/esm/locale/*.js")

export async function loadDayjsLocale(language) {
	let locale = (language || "en").toLowerCase().replace(/_/g, "-")
	let loadLocale = locales[`../../node_modules/dayjs/esm/locale/${locale}.js`]

	while (!loadLocale && locale.includes("-")) {
		locale = locale.slice(0, locale.lastIndexOf("-"))
		loadLocale = locales[`../../node_modules/dayjs/esm/locale/${locale}.js`]
	}

	dayjs.locale("en")
	if (!loadLocale || locale === "en") return

	try {
		const { default: localeData } = await loadLocale()
		dayjs.locale(localeData)
	} catch (error) {
		console.error(`Failed to load Day.js locale ${locale}:`, error)
	}
}

export default dayjs
