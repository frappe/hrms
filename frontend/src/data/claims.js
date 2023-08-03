import { createResource } from "frappe-ui"
import { employeeResource } from "./employee"

const transformClaimData = (data) => {
	return data.map((claim) => {
		claim.doctype = "Expense Claim"
		return claim
	})
}

export const myRequests = createResource({
	url: "hrms.api.get_expense_claims",
	params: {
		employee: employeeResource.data.name,
		limit: 5,
	},
	auto: true,
	transform(data) {
		return transformClaimData(data)
	},
})

export const teamRequests = createResource({
	url: "hrms.api.get_expense_claims",
	params: {
		employee: employeeResource.data.name,
		approver_id: employeeResource.data.user_id,
		for_approval: 1,
		limit: 5,
	},
	auto: true,
	transform(data) {
		return transformClaimData(data)
	},
})
