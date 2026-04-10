import { createResource } from "frappe-ui"

const companyCurrency = createResource({
	url: "hrms.api.get_company_currencies",
	auto: true,
})

const currencySymbols = createResource({
	url: "hrms.api.get_currency_symbols",
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

export const currencyPrecision = createResource({
	url: "frappe.client.get_single_value",
	params: {
		doctype: "System Settings",
		field: "currency_precision"
	},
	auto: true,
	initialData: 2
});