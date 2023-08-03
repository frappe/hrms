import { createResource } from "frappe-ui"

const currencies = createResource({
	url: "hrms.api.get_company_currencies",
	auto: true,
})

export function getCompanyCurrency(company) {
	return currencies?.data?.[company]
}
