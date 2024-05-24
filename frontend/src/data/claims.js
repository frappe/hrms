import { createResource } from "frappe-ui"
import { employeeResource } from "./employee"
import { reactive } from "vue"
import dayjs from "@/utils/dayjs"

export const expenseClaimSummary = createResource({
	url: "hrms.api.get_expense_claim_summary",
	makeParams(params) {
		return {
			employee: employeeResource.data.name,
			start_date: params ? params.year_start_date : null,
			end_date: params ? params.year_end_date : null,
		}
	},
	auto: true,
})

function getPeriodLabel(period) {
	return `${dayjs(period?.year_start_date).format("MMM YYYY")} - ${dayjs(
		period?.year_end_date
	).format("MMM YYYY")}`
}

const add_options = (period) => {
	return {
		...period,
		value: getPeriodLabel(period),
		label: getPeriodLabel(period),
	}
}

export const fiscalYears = createResource({
	url: "hrms.api.get_fiscal_years_for_company",
	params: {
		company: employeeResource.data?.company,
		current_date: dayjs().format("YYYY-MM-DD"),
	},
	auto: true,
	transform: (data) => {
		const newdata = {
			current_fiscal_year: add_options(data.current_fiscal_year),
			fiscal_years: data.fiscal_years.map((period) => {
				return add_options(period)
			}),
		}
		return newdata
	},
})

const transformClaimData = (data) => {
	return data.map((claim) => {
		claim.doctype = "Expense Claim"
		return claim
	})
}

export const myClaims = createResource({
	url: "hrms.api.get_expense_claims",
	params: {
		employee: employeeResource.data.name,
		limit: 10,
	},
	auto: true,
	cache: "hrms:my_claims",
	transform(data) {
		return transformClaimData(data)
	},
	onSuccess() {
		expenseClaimSummary.reload()
	},
})

export const teamClaims = createResource({
	url: "hrms.api.get_expense_claims",
	params: {
		employee: employeeResource.data.name,
		approver_id: employeeResource.data.user_id,
		for_approval: 1,
		limit: 10,
	},
	auto: true,
	cache: "hrms:team_claims",
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
