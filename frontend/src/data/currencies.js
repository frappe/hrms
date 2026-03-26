import { createResource } from "frappe-ui"

const companyCurrency = createResource({
	url: "hr_app.api.get_company_currencies",
	auto: true,
})

const currencySymbols = createResource({
	url: "hr_app.api.get_currency_symbols",
	auto: true,
})

export function getCompanyCurrency(company) {
	return companyCurrency?.data?.[company]?.[0]
}

export function getCompanyCurrencySymbol(company) {
	return companyCurrency?.data?.[company]?.[1]
}

export function getCurrencySymbol(currency) {
	return currencySymbols?.data?.[currency]
}
