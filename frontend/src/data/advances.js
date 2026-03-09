import { createResource } from "frappe-ui"

const transformAdvanceData = (data) => {
	return data.map((claim) => {
		claim.doctype = "Employee Advance"
		return claim
	})
}

export const advanceBalance = createResource({
	url: "hrms.api.get_employee_advance_balance",
	auto: true,
	cache: "hrms:employee_advance_balance",
	transform(data) {
		return transformAdvanceData(data)
	},
})
