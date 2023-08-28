import { createResource } from "frappe-ui"
import { getEmployee } from "./employee"
import { reactive } from "vue"

const transformClaimData = (data) => {
	return data.map((claim) => {
		claim.doctype = "Expense Claim"
		return claim
	})
}

const employee = getEmployee()

export const myClaims = createResource({
	url: "hrms.api.get_expense_claims",
	params: {
		employee: employee.name,
		limit: 5,
	},
	auto: true,
	transform(data) {
		return transformClaimData(data)
	},
})

export const teamClaims = createResource({
	url: "hrms.api.get_expense_claims",
	params: {
		employee: employee.name,
		approver_id: employee.user_id,
		for_approval: 1,
		limit: 5,
	},
	auto: true,
	transform(data) {
		return transformClaimData(data)
	},
})

export let claimTypesByID = reactive({})

export const claimTypesResource = createResource({
	url: "hrms.api.get_expense_claim_types",
	auto: true,
	transform(data) {
		return data.map((row) => {
			claimTypesByID[row.name] = row
			return row
		})
	},
})
